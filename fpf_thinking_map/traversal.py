"""Agentic traversal engine — the LLM's guided reasoning loop.

Step 4-6 of the agentic run:
4. LLM reasons over the active map (not inventing semantics — navigating)
5. Deterministic checks validate (guards + logic)
6. Agent chooses outcome

Horizontal design (#6, #25):
- step() takes optional transition_id — evaluates one move, not the whole board
- demo_walk() replaces full_run() — explicitly a demo, not operational
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
    ABSTAIN = "abstain"
    ESCALATE = "escalate"
    PUBLISH = "publish"
    REVISE_PLAN = "revise_plan"
    COLLECT_EVIDENCE = "collect_evidence"
    CHANGE_FRAME = "change_frame"


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

    def _build_prompt(self, state: ActiveState, logic_ctx: dict, transition_id: str | None = None) -> dict:
        if transition_id:
            prompt = state.slice(transition_id)
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
    ) -> Outcome:
        """#6: one traversal step, optionally focused on a specific transition.

        With transition_id: evaluates only that move's gate, evidence, guards.
        Without: scans possible transitions from current state.
        """
        if not state.active_context:
            return Outcome(
                kind=OutcomeKind.CHANGE_FRAME,
                reason="No active context bound — select a bounded context first",
                llm_prompt_state=state.to_llm_prompt_state(),
            )

        if transition_id:
            t = self.semantic_map.transitions.get(transition_id)
            ctx_id = state.binding.active_context_id
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
                    llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
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
                    llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
                )
            return Outcome(
                kind=OutcomeKind.ABSTAIN,
                reason=f"Guards deny, no evidence path: {'; '.join(denials)}",
                warnings=warnings,
                llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
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
                llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
            )

        transitions = state.possible_transitions
        if not transitions:
            if state.binding.candidate_actions:
                return Outcome(
                    kind=OutcomeKind.CONTINUE,
                    reason="No transitions but actions available",
                    warnings=warnings,
                    llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
                )
            return Outcome(
                kind=OutcomeKind.ASK,
                reason="No transitions, no actions — need input",
                warnings=warnings,
                llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
            )

        return Outcome(
            kind=OutcomeKind.CONTINUE,
            reason="Guards pass, evidence sufficient, transitions available",
            warnings=warnings,
            llm_prompt_state=self._build_prompt(state, logic_ctx, transition_id),
        )

    def attempt_transition(
        self,
        state: ActiveState,
        transition_id: str,
    ) -> Outcome:
        """Attempt a specific transition. Guards scoped to this move."""
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

        if state.transition_to(transition_id):
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
                OutcomeKind.CHANGE_FRAME,
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
