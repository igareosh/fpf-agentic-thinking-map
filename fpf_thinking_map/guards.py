"""Deterministic guard engine — the constraint layer.

Step 5 of the agentic run: before action or publication,
deterministic checks validate the move is lawful.

These are NOT LLM judgments. These are hard checks that
the LLM cannot override. The semantic circuit breakers.

Horizontal design (#19):
- Guards declare what they apply to (transition, role, gate, global)
- Engine evaluates only guards relevant to the current move
- No ambient totality — nothing inspects everything unless asked
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from fpf_thinking_map.primitives import (
    GateDecision,
    Freshness,
)
from fpf_thinking_map.state import ActiveState


class GuardVerdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


class GuardScope(Enum):
    """What a guard applies to — used for focused evaluation (#19)."""
    TRANSITION = "transition"
    ROLE = "role"
    EVIDENCE = "evidence"
    GLOBAL = "global"


@dataclass
class GuardResult:
    guard_name: str
    verdict: GuardVerdict
    reason: str = ""


@dataclass
class Guard:
    """A named guard with declared scope."""
    name: str
    scope: GuardScope
    fn: Callable[[ActiveState, str | None], GuardResult]

    def evaluate(self, state: ActiveState, transition_id: str | None = None) -> GuardResult:
        return self.fn(state, transition_id)


# ---------------------------------------------------------------------------
# Built-in guard functions — compiled from FPF normative constraints
# ---------------------------------------------------------------------------

def _guard_commitment_evidence(state: ActiveState, transition_id: str | None) -> GuardResult:
    """FPF A.2.8 + A.10: binding commitments on this move need evidence.

    #3: per-transition check, not context-wide.
    """
    if not transition_id:
        return GuardResult("commitment_evidence", GuardVerdict.ALLOW)

    missing = state.missing_evidence_for(transition_id)
    if missing:
        return GuardResult(
            "commitment_evidence",
            GuardVerdict.WARN,
            f"Transition '{transition_id}' missing evidence: {missing}",
        )
    return GuardResult("commitment_evidence", GuardVerdict.ALLOW)


def _guard_planning_not_enactment(state: ActiveState, transition_id: str | None) -> GuardResult:
    """FPF A.4 + A.7: planning ≠ enactment."""
    if not transition_id:
        return GuardResult("planning_not_enactment", GuardVerdict.ALLOW)

    t = state.semantic_map.transitions.get(transition_id)
    if not t:
        return GuardResult("planning_not_enactment", GuardVerdict.ALLOW)

    if t.to_state.endswith("_done") or t.to_state.endswith("_complete"):
        ctx_id = state.binding.active_context_id or ""
        has_enactment = any(
            w.context_id == ctx_id
            for w in state.semantic_map.work_records.values()
        )
        if not has_enactment:
            return GuardResult(
                "planning_not_enactment",
                GuardVerdict.DENY,
                "Cannot transition to done/complete without enactment work records",
            )
    return GuardResult("planning_not_enactment", GuardVerdict.ALLOW)


def _guard_role_conflict(state: ActiveState, _transition_id: str | None) -> GuardResult:
    """FPF A.2.7: incompatible roles cannot be active simultaneously."""
    active = state.active_roles
    for i, r1 in enumerate(active):
        for r2 in active[i + 1:]:
            if r1.conflicts_with(r2.role_id) or r2.conflicts_with(r1.role_id):
                return GuardResult(
                    "role_conflict",
                    GuardVerdict.DENY,
                    f"Roles '{r1.label}' and '{r2.label}' are incompatible (⊥)",
                )
    return GuardResult("role_conflict", GuardVerdict.ALLOW)


def _guard_gate_pass(state: ActiveState, transition_id: str | None) -> GuardResult:
    """FPF A.21: gate for this transition must pass.

    #2: only checks the gate on the specific transition, not all gates in context.
    """
    if not transition_id:
        return GuardResult("gate_pass", GuardVerdict.ALLOW)

    gate = state.gate_for_transition(transition_id)
    if not gate:
        return GuardResult("gate_pass", GuardVerdict.ALLOW)

    decision = gate.evaluate(state.available_evidence_ids)
    if decision == GateDecision.BLOCK:
        return GuardResult(
            "gate_pass",
            GuardVerdict.DENY,
            f"Gate '{gate.gate_id}' blocks — hard denial",
        )
    if decision == GateDecision.ABSTAIN:
        return GuardResult(
            "gate_pass",
            GuardVerdict.DENY,
            f"Gate '{gate.gate_id}' abstains — insufficient evidence",
        )
    if decision == GateDecision.DEGRADE:
        return GuardResult(
            "gate_pass",
            GuardVerdict.WARN,
            f"Gate '{gate.gate_id}' degraded — proceed with caution",
        )
    return GuardResult("gate_pass", GuardVerdict.ALLOW)


def _guard_scope_check(state: ActiveState, _transition_id: str | None) -> GuardResult:
    """FPF A.2.6 (USM): actions must stay within context scope."""
    ctx = state.active_context
    if not ctx:
        return GuardResult("scope_check", GuardVerdict.WARN, "No active context")

    for action in state.binding.candidate_actions:
        if "/" in action:
            target_ctx = action.split("/")[0]
            if target_ctx != ctx.context_id:
                has_bridge = any(
                    b.target_context_id == target_ctx for b in ctx.bridges_to
                )
                if not has_bridge:
                    return GuardResult(
                        "scope_check",
                        GuardVerdict.DENY,
                        f"Action '{action}' crosses to '{target_ctx}' without bridge",
                    )
    return GuardResult("scope_check", GuardVerdict.ALLOW)


def _guard_evidence_freshness(state: ActiveState, transition_id: str | None) -> GuardResult:
    """FPF B.3.4: stale evidence triggers warning. #20: uses Freshness enum.

    Uses effective_freshness() which factors in TTL decay over traversal steps.
    """
    if transition_id:
        t = state.semantic_map.transitions.get(transition_id)
        check_ids = set(t.required_evidence) if t else set()
    else:
        check_ids = state.available_evidence_ids

    for eid in check_ids & state.available_evidence_ids:
        freshness = state.effective_freshness(eid)
        if freshness in (Freshness.STALE, Freshness.EXPIRED):
            ev = state.semantic_map.evidence.get(eid)
            label = ev.label if ev else eid
            return GuardResult(
                "evidence_freshness",
                GuardVerdict.WARN,
                f"Evidence '{label}' is {freshness.value}",
            )
    return GuardResult("evidence_freshness", GuardVerdict.ALLOW)


def _guard_expired_assignment(state: ActiveState, _transition_id: str | None) -> GuardResult:
    """R07/R08: expired role assignments must not authorize work.

    If the map has role assignments and any active assignment is expired,
    deny. This catches assignments that became invalid between binding
    and execution.
    """
    if not state.semantic_map.role_assignments:
        return GuardResult("expired_assignment", GuardVerdict.ALLOW)

    ctx_id = state.binding.active_context_id
    actor = state.binding.actor
    for ra in state.semantic_map.role_assignments.values():
        if ra.holder_id == actor and (not ctx_id or ra.context_id == ctx_id):
            if ra.expired:
                return GuardResult(
                    "expired_assignment",
                    GuardVerdict.DENY,
                    f"Role assignment '{ra.assignment_id}' for role '{ra.role_id}' is expired",
                )
    return GuardResult("expired_assignment", GuardVerdict.ALLOW)


def _guard_speech_act_validity(state: ActiveState, _transition_id: str | None) -> GuardResult:
    """R20/R21: speech acts referenced as evidence must not be expired.

    If evidence IDs reference speech acts (approvals, authorizations),
    check they haven't been revoked or expired.
    """
    for eid in state.available_evidence_ids:
        sa = state.semantic_map.speech_acts.get(eid)
        if sa and sa.expired:
            return GuardResult(
                "speech_act_validity",
                GuardVerdict.DENY,
                f"Speech act '{sa.act_id}' ({sa.act_type.value}) is expired/revoked",
            )
    return GuardResult("speech_act_validity", GuardVerdict.ALLOW)


def _guard_context_invariants(state: ActiveState, _transition_id: str | None) -> GuardResult:
    """R05: context invariants must be surfaced for evaluation.

    Invariants are context-local constraints. If the active context has
    invariants, they are flagged as warnings so the model considers them.
    """
    ctx = state.active_context
    if not ctx or not ctx.invariants:
        return GuardResult("context_invariants", GuardVerdict.ALLOW)

    return GuardResult(
        "context_invariants",
        GuardVerdict.WARN,
        f"Context '{ctx.context_id}' has invariants: {ctx.invariants}",
    )


# ---------------------------------------------------------------------------
# Built-in guard registry
# ---------------------------------------------------------------------------

BUILTIN_GUARDS = [
    Guard("commitment_evidence", GuardScope.TRANSITION, _guard_commitment_evidence),
    Guard("planning_not_enactment", GuardScope.TRANSITION, _guard_planning_not_enactment),
    Guard("role_conflict", GuardScope.ROLE, _guard_role_conflict),
    Guard("gate_pass", GuardScope.TRANSITION, _guard_gate_pass),
    Guard("scope_check", GuardScope.GLOBAL, _guard_scope_check),
    Guard("evidence_freshness", GuardScope.EVIDENCE, _guard_evidence_freshness),
    Guard("context_invariants", GuardScope.GLOBAL, _guard_context_invariants),
    Guard("expired_assignment", GuardScope.ROLE, _guard_expired_assignment),
    Guard("speech_act_validity", GuardScope.EVIDENCE, _guard_speech_act_validity),
]


# ---------------------------------------------------------------------------
# Guard engine
# ---------------------------------------------------------------------------

@dataclass
class GuardEngine:
    """Runs guards against an active state.

    #19: supports focused evaluation — pass transition_id to only
    run guards relevant to that move. Without it, runs all.
    """
    guards: list[Guard] = field(default_factory=lambda: list(BUILTIN_GUARDS))

    def add_guard(self, guard: Guard) -> None:
        self.guards.append(guard)

    def evaluate(
        self,
        state: ActiveState,
        transition_id: str | None = None,
        scopes: set[GuardScope] | None = None,
    ) -> list[GuardResult]:
        """#19: evaluate guards filtered by scope and/or transition."""
        results = []
        for g in self.guards:
            if scopes and g.scope not in scopes:
                continue
            results.append(g.evaluate(state, transition_id))
        return results

    def is_action_allowed(
        self,
        state: ActiveState,
        transition_id: str | None = None,
    ) -> tuple[bool, list[GuardResult]]:
        results = self.evaluate(state, transition_id)
        denied = [r for r in results if r.verdict == GuardVerdict.DENY]
        return (len(denied) == 0, results)

    def denied_reasons(self, state: ActiveState, transition_id: str | None = None) -> list[str]:
        results = self.evaluate(state, transition_id)
        return [r.reason for r in results if r.verdict == GuardVerdict.DENY]

    def warnings(self, state: ActiveState, transition_id: str | None = None) -> list[str]:
        results = self.evaluate(state, transition_id)
        return [r.reason for r in results if r.verdict == GuardVerdict.WARN]
