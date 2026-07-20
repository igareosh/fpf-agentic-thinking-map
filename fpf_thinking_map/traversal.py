"""Traversal engine — the LLM's guided reasoning loop.

step() evaluates one move: checks context, logic, guards, evidence, transitions.
Returns one of 10 outcomes:

  CONTINUE         — transitions available, guards pass, proceed
  COLLECT_EVIDENCE — evidence gaps block the move, here's what's missing
  IDLE             — at rest, nothing actionable (not stuck — done)
  BRIDGE           — dead-ended in context, bridge to another context available
  ASK              — stuck, need external input
  ABSTAIN          — guards deny with no evidence path, or logic contradiction
  ESCALATE         — risk threshold exceeded
  CHANGE_FRAME     — no active context bound
  PUBLISH          — publication move
  REVISE_PLAN      — plan needs revision

Each step() increments the hop counter, driving TTL evidence decay.
The model reads the outcome JSON and picks the next move — no re-reasoning
about epistemic state the code already computed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fpf_thinking_map.primitives import GateDecision
from fpf_thinking_map.state import ActiveState, SemanticMap, RuntimeBinding
from fpf_thinking_map.guards import GuardEngine, GuardVerdict
from fpf_thinking_map.logic import LogicLayer


class OutcomeKind(Enum):
    """The agent's lawful moves — FPF-bounded outcome space."""
    CONTINUE = "continue"
    ASK = "ask"
    ABSTAIN = "denied"
    ESCALATE = "escalate"
    PUBLISH = "publish"
    REVISE_PLAN = "revise_plan"
    COLLECT_EVIDENCE = "collect_evidence"
    CHANGE_FRAME = "change_frame"
    IDLE = "idle"
    BRIDGE = "bridge"


@dataclass
class Outcome:
    """The result of one traversal step."""
    kind: OutcomeKind
    reason: str = ""
    next_state: str | None = None
    action: str | None = None
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    llm_prompt_state: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "outcome": self.kind.value,
            "reason": self.reason,
        }
        if self.next_state:
            d["next_state"] = self.next_state
        if self.action:
            d["action"] = self.action
        if self.missing_evidence:
            d["missing_evidence"] = self.missing_evidence
        if self.warnings:
            d["warnings"] = self.warnings
        return d


class ThinkingMapTraversal:
    """The agentic traversal engine.

    Usage:
        1. Build a SemanticMap (load compiled primitives)
        2. Create a RuntimeBinding (bind inputs)
        3. Create ThinkingMapTraversal(semantic_map)
        4. Call step(state) or step(state, transition_id) — returns Outcome
        5. LLM reads Outcome, decides next move
        6. Repeat until terminal outcome
    """

    def __init__(
        self,
        semantic_map: SemanticMap,
        guard_engine: GuardEngine | None = None,
        logic_layer: LogicLayer | None = None,
    ):
        self.semantic_map = semantic_map
        self.guard_engine = guard_engine or GuardEngine()
        self.logic_layer = logic_layer

    def build_active_state(
        self,
        binding: RuntimeBinding,
        current_state: str = "initial",
    ) -> ActiveState:
        return ActiveState(
            semantic_map=self.semantic_map,
            binding=binding,
            current_state=current_state,
        )

    def _build_prompt(
        self,
        state: ActiveState,
        logic_ctx: dict,
        transition_id: str | None = None,
        guard_blockers: list[str] | None = None,
        include_full_state: bool = True,
    ) -> dict:
        """#27: include_full_state=False ships the A-RAG "chunk read" alone.

        A caller that already knows its transition_id doesn't need the whole
        board bolted on — that's the win slice() was built for in the first
        place. Default stays True so every existing caller sees identical
        output; opt out only when you want the lean payload.
        """
        if transition_id:
            prompt = state.slice(transition_id, guard_blockers=guard_blockers)
            if include_full_state:
                prompt["full_state"] = state.to_llm_prompt_state()
        else:
            prompt = state.to_llm_prompt_state()
        if logic_ctx:
            prompt["logic"] = logic_ctx
        return prompt

    def _eval_logic(self, state: ActiveState, tags: set[str] | None = None) -> dict:
        if not self.logic_layer:
            return {}
        return self.logic_layer.to_llm_context(state, tags)

    def step(
        self,
        state: ActiveState,
        transition_id: str | None = None,
        logic_tags: set[str] | None = None,
        include_full_state: bool = True,
    ) -> Outcome:
        """#6: one traversal step, optionally focused on a specific transition.

        With transition_id: evaluates only that move's gate, evidence, guards.
        Without: scans possible transitions from current state.

        Increments step_count each call — drives TTL evidence decay.

        include_full_state=False (only meaningful together with transition_id):
        ships the scoped slice without the full board — see #27 in _build_prompt.

        Thin wrapper around _step_inner(): appends an "attention, human still
        waiting" warning whenever state.pending_authorization is set, no
        matter which move is being considered here. This never blocks the
        move under evaluation — a pending ask elsewhere is surfaced, not
        enforced, the same way ADV-01's evidence-staleness WARN doesn't
        block either. Enforcing "nothing else moves until this is resolved"
        is a real policy some harnesses may want, but it's an app-level
        decision, not one this domain-agnostic engine should force.
        """
        outcome = self._step_inner(state, transition_id, logic_tags, include_full_state)
        if state.pending_authorization:
            outcome.warnings.append(
                f"transition '{state.pending_authorization}' is still awaiting "
                f"human authorization, unresolved"
            )
        return outcome

    def _step_inner(
        self,
        state: ActiveState,
        transition_id: str | None = None,
        logic_tags: set[str] | None = None,
        include_full_state: bool = True,
    ) -> Outcome:
        state.step_count += 1

        if not state.active_context:
            return Outcome(
                kind=OutcomeKind.CHANGE_FRAME,
                reason="No active context bound — select a bounded context first",
                llm_prompt_state=state.to_llm_prompt_state(),
            )

        state.register_visit()

        ctx_id = state.binding.active_context_id or ""

        if transition_id:
            t = self.semantic_map.transitions.get(transition_id)
            if t and ctx_id and t.context_id != ctx_id:
                return Outcome(
                    kind=OutcomeKind.ABSTAIN,
                    reason=f"Transition '{transition_id}' belongs to context "
                           f"'{t.context_id}', active is '{ctx_id}'",
                )

        logic_ctx = self._eval_logic(state, logic_tags)
        if logic_ctx:
            consistency = logic_ctx.get("consistency", {})
            if not consistency.get("consistent", True):
                return Outcome(
                    kind=OutcomeKind.ABSTAIN,
                    reason=f"Logic contradiction: {consistency.get('contradictions', [])}",
                    warnings=consistency.get("contradictions", []),
                    llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id, include_full_state=include_full_state),
                )

        allowed, guard_results = self.guard_engine.is_action_allowed(state, transition_id)
        warnings = [r.reason for r in guard_results if r.verdict == GuardVerdict.WARN]
        denials = [r.reason for r in guard_results if r.verdict == GuardVerdict.DENY]

        if not allowed:
            if transition_id:
                missing = state.missing_evidence_for(transition_id)
            else:
                missing = state.missing_evidence
            if missing:
                return Outcome(
                    kind=OutcomeKind.COLLECT_EVIDENCE,
                    reason=f"Guards deny: {'; '.join(denials)}",
                    missing_evidence=missing,
                    warnings=warnings,
                    llm_prompt_state=self._build_prompt(
                        state, logic_ctx, transition_id,
                        guard_blockers=denials, include_full_state=include_full_state,
                    ),
                )
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Guards deny, no evidence path: {'; '.join(denials)}",
                warnings=warnings,
                llm_prompt_state=self._build_prompt(
                    state, logic_ctx, transition_id, guard_blockers=denials,
                ),
            )

        if transition_id:
            missing = state.missing_evidence_for(transition_id)
        else:
            missing = state.missing_evidence
        if missing:
            return Outcome(
                kind=OutcomeKind.COLLECT_EVIDENCE,
                reason=f"Evidence gaps: {missing}",
                missing_evidence=missing,
                warnings=warnings,
                llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id, include_full_state=include_full_state),
            )

        transitions = state.possible_transitions
        if not transitions:
            if state.binding.candidate_actions:
                return Outcome(
                    kind=OutcomeKind.CONTINUE,
                    reason="No transitions but actions available",
                    warnings=warnings,
                    llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id, include_full_state=include_full_state),
                )

            bridge_opts = self.semantic_map.bridge_options(ctx_id)
            if bridge_opts:
                prompt = state.to_llm_prompt_state()
                prompt["bridge_options"] = bridge_opts
                if logic_ctx:
                    prompt["logic"] = logic_ctx
                return Outcome(
                    kind=OutcomeKind.BRIDGE,
                    reason=f"No transitions in '{ctx_id}' from '{state.current_state}', "
                           f"bridges available to: "
                           f"{', '.join(opt['target_context'] for opt in bridge_opts)}",
                    warnings=warnings,
                    llm_prompt_state=prompt,
                )

            return Outcome(
                kind=OutcomeKind.IDLE,
                reason="At rest — no transitions, no actions, no bridges",
                warnings=warnings,
                llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id, include_full_state=include_full_state),
            )

        return Outcome(
            kind=OutcomeKind.CONTINUE,
            reason="Guards pass, evidence sufficient, transitions available",
            warnings=warnings,
            llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id, include_full_state=include_full_state),
        )

    def attempt_transition(
        self,
        state: ActiveState,
        transition_id: str,
        authorized: bool = False,
    ) -> Outcome:
        """Attempt a specific transition. Guards scoped to this move.

        authorized=True is required to fire a requires_human_authorization transition —
        the model requesting the same transition_id without it gets
        ESCALATE, not a silent no-op and not a bypass.
        """
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Transition '{transition_id}' not found",
            )

        ctx_id = state.binding.active_context_id
        if ctx_id and t.context_id != ctx_id:
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Transition '{transition_id}' belongs to context '{t.context_id}', "
                       f"active is '{ctx_id}'",
            )

        if t.from_state != state.current_state:
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Transition requires state '{t.from_state}', current is '{state.current_state}'",
            )

        if t.requires_human_authorization and not authorized:
            missing_now = state.missing_evidence_for(transition_id)
            reason = (
                f"Transition '{transition_id}' is requires_human_authorization — "
                f"requires explicit human authorization, not model-invoked"
            )
            if missing_now:
                reason += f" (also missing evidence: {missing_now})"
            state.pending_authorization = transition_id
            return Outcome(
                kind=OutcomeKind.ESCALATE,
                reason=reason,
                missing_evidence=missing_now,
            )

        missing = state.missing_evidence_for(transition_id)
        if missing:
            return Outcome(
                kind=OutcomeKind.COLLECT_EVIDENCE,
                reason=f"Transition '{transition_id}' missing evidence: {missing}",
                missing_evidence=missing,
            )

        if t.required_gate_id:
            gate = self.semantic_map.gates.get(t.required_gate_id)
            if gate:
                decision = gate.evaluate(state.available_evidence_ids)
                if decision == GateDecision.BLOCK:
                    return Outcome(
                        kind=OutcomeKind.ABSTAIN,
                        reason=f"Gate '{t.required_gate_id}' blocks — hard denial",
                    )
                if decision == GateDecision.ABSTAIN:
                    return Outcome(
                        kind=OutcomeKind.COLLECT_EVIDENCE,
                        reason=f"Gate '{t.required_gate_id}' abstains — collect evidence",
                        missing_evidence=gate.missing_evidence(state.available_evidence_ids),
                    )

        allowed, guard_results = self.guard_engine.is_action_allowed(state, transition_id)
        if not allowed:
            denials = [r.reason for r in guard_results if r.verdict == GuardVerdict.DENY]
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Guards deny: {'; '.join(denials)}",
            )

        if state.transition_to(transition_id, authorized=authorized):
            logic_ctx = self._eval_logic(state)
            return Outcome(
                kind=OutcomeKind.CONTINUE,
                reason=f"Transitioned to '{t.to_state}'",
                next_state=t.to_state,
                llm_prompt_state=self._build_prompt(state, logic_ctx),
            )

        return Outcome(
            kind=OutcomeKind.ABSTAIN,
            reason="Transition failed",
        )

    def attempt_bridge(
        self,
        state: ActiveState,
        target_context_id: str,
        entry_state: str,
    ) -> Outcome:
        """#26: enact a bridge crossing the BRIDGE outcome only advertised.

        step() surfaces bridge_options() as advisory metadata; this is the
        enactment half — it enforces the bridge's fidelity contract
        (substitution_license vs. risk_level) before mutating state, then
        performs the crossing. An unlicensed bridge under high/critical risk
        is refused as ESCALATE, not silently allowed.
        """
        ok, reason = state.cross_bridge(target_context_id, entry_state)
        if not ok:
            kind = OutcomeKind.ESCALATE if "unlicensed" in reason else OutcomeKind.ABSTAIN
            return Outcome(kind=kind, reason=reason)

        logic_ctx = self._eval_logic(state)
        return Outcome(
            kind=OutcomeKind.CONTINUE,
            reason=reason,
            next_state=state.current_state,
            llm_prompt_state=self._build_prompt(state, logic_ctx),
        )

    def demo_walk(
        self,
        binding: RuntimeBinding,
        max_steps: int = 20,
    ) -> list[Outcome]:
        """#25: explicitly a demo/test walk — auto-takes first transition.

        Not operational. For operational use, call step() + attempt_transition()
        with explicit transition_id chosen by the LLM.
        """
        state = self.build_active_state(binding)
        outcomes: list[Outcome] = []

        for _ in range(max_steps):
            outcome = self.step(state)
            outcomes.append(outcome)

            if outcome.kind in (
                OutcomeKind.ABSTAIN, OutcomeKind.ASK, OutcomeKind.ESCALATE,
                OutcomeKind.PUBLISH, OutcomeKind.COLLECT_EVIDENCE,
                OutcomeKind.CHANGE_FRAME, OutcomeKind.IDLE, OutcomeKind.BRIDGE,
            ):
                break

            transitions = state.possible_transitions
            if transitions:
                t_outcome = self.attempt_transition(state, transitions[0].transition_id)
                outcomes.append(t_outcome)
                if t_outcome.kind != OutcomeKind.CONTINUE:
                    break
            else:
                break

        return outcomes
