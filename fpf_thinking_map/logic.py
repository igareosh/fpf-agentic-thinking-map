"""Propositional logic glue layer for agentic small-step decisions.

The 6 fundamental logic functions from informatics/computational logic
(Mitev L., Bazele programării logice) integrated as deterministic
decision glue in the thinking map.

Horizontal design (#8-#13, #21):
- Rules have kinds: block, warn, route, hint
- Rules have tags for bundle-based evaluation
- Rules declare exclusive_with for tag-based contradiction detection
- LogicLayer evaluates only rules matching requested tags
- Implication rules only emit actions when antecedent is true (no vacuous emission)
- Risk-sensitive flag controls risk_level visibility per rule
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from fpf_thinking_map.state import ActiveState
from fpf_thinking_map.primitives import GateDecision, Freshness


# ---------------------------------------------------------------------------
# Propositional atoms — facts extracted from active state
# ---------------------------------------------------------------------------

class Prop:
    """A proposition about the current state."""

    def evaluate(self, state: ActiveState) -> bool:
        raise NotImplementedError

    def NOT(self) -> NotProp:
        return NotProp(self)

    def AND(self, other: Prop) -> AndProp:
        return AndProp(self, other)

    def OR(self, other: Prop) -> OrProp:
        return OrProp(self, other)

    def XOR(self, other: Prop) -> XorProp:
        return XorProp(self, other)

    def IMPLIES(self, other: Prop) -> ImpliesProp:
        return ImpliesProp(self, other)

    def IFF(self, other: Prop) -> IffProp:
        return IffProp(self, other)

    def __repr__(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# The 6 operators as compound propositions
# ---------------------------------------------------------------------------

@dataclass
class NotProp(Prop):
    """¬p — true when p is false."""
    operand: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return not self.operand.evaluate(state)

    def __repr__(self) -> str:
        return f"¬({self.operand})"


@dataclass
class AndProp(Prop):
    """p ∧ q — true when both p and q are true."""
    left: Prop
    right: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return self.left.evaluate(state) and self.right.evaluate(state)

    def __repr__(self) -> str:
        return f"({self.left} ∧ {self.right})"


@dataclass
class OrProp(Prop):
    """p ∨ q — true when at least one of p, q is true."""
    left: Prop
    right: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return self.left.evaluate(state) or self.right.evaluate(state)

    def __repr__(self) -> str:
        return f"({self.left} ∨ {self.right})"


@dataclass
class XorProp(Prop):
    """p ⊕ q — true when exactly one of p, q is true."""
    left: Prop
    right: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return self.left.evaluate(state) != self.right.evaluate(state)

    def __repr__(self) -> str:
        return f"({self.left} ⊕ {self.right})"


@dataclass
class ImpliesProp(Prop):
    """p → q — false only when p is true and q is false."""
    antecedent: Prop
    consequent: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return (not self.antecedent.evaluate(state)) or self.consequent.evaluate(state)

    def __repr__(self) -> str:
        return f"({self.antecedent} → {self.consequent})"


@dataclass
class IffProp(Prop):
    """p ↔ q — true when both have the same truth value."""
    left: Prop
    right: Prop

    def evaluate(self, state: ActiveState) -> bool:
        return self.left.evaluate(state) == self.right.evaluate(state)

    def __repr__(self) -> str:
        return f"({self.left} ↔ {self.right})"


# ---------------------------------------------------------------------------
# Atomic propositions — facts about the active state
# ---------------------------------------------------------------------------

@dataclass
class EvidencePresent(Prop):
    evidence_id: str

    def evaluate(self, state: ActiveState) -> bool:
        return self.evidence_id in state.available_evidence_ids

    def __repr__(self) -> str:
        return f"evidence({self.evidence_id})"


@dataclass
class GatePasses(Prop):
    gate_id: str

    def evaluate(self, state: ActiveState) -> bool:
        gate = state.semantic_map.gates.get(self.gate_id)
        if not gate:
            return False
        return gate.evaluate(state.available_evidence_ids) == GateDecision.PASS

    def __repr__(self) -> str:
        return f"gate_pass({self.gate_id})"


@dataclass
class GateBlocked(Prop):
    gate_id: str

    def evaluate(self, state: ActiveState) -> bool:
        gate = state.semantic_map.gates.get(self.gate_id)
        if not gate:
            return True
        return gate.evaluate(state.available_evidence_ids) == GateDecision.ABSTAIN

    def __repr__(self) -> str:
        return f"gate_blocked({self.gate_id})"


@dataclass
class RoleActive(Prop):
    role_id: str

    def evaluate(self, state: ActiveState) -> bool:
        return any(r.role_id == self.role_id for r in state.active_roles)

    def __repr__(self) -> str:
        return f"role({self.role_id})"


@dataclass
class InState(Prop):
    expected_state: str

    def evaluate(self, state: ActiveState) -> bool:
        return state.current_state == self.expected_state

    def __repr__(self) -> str:
        return f"state({self.expected_state})"


@dataclass
class CommitmentMet(Prop):
    commitment_id: str

    def evaluate(self, state: ActiveState) -> bool:
        c = state.semantic_map.commitments.get(self.commitment_id)
        if not c:
            return False
        return all(eid in state.available_evidence_ids for eid in c.evidence_refs)

    def __repr__(self) -> str:
        return f"commitment_met({self.commitment_id})"


@dataclass
class HasMissingEvidence(Prop):
    def evaluate(self, state: ActiveState) -> bool:
        return len(state.missing_evidence) > 0

    def __repr__(self) -> str:
        return "has_missing_evidence"


@dataclass
class RiskAbove(Prop):
    threshold: str
    _levels: dict[str, int] = field(
        default_factory=lambda: {"low": 0, "normal": 1, "high": 2, "critical": 3}
    )

    def evaluate(self, state: ActiveState) -> bool:
        current = self._levels.get(state.binding.risk_level, 1)
        threshold = self._levels.get(self.threshold, 1)
        return current >= threshold

    def __repr__(self) -> str:
        return f"risk≥{self.threshold}"


@dataclass
class TransitionAvailable(Prop):
    transition_id: str

    def evaluate(self, state: ActiveState) -> bool:
        return any(
            t.transition_id == self.transition_id
            for t in state.possible_transitions
        )

    def __repr__(self) -> str:
        return f"transition({self.transition_id})"


@dataclass
class CustomProp(Prop):
    name: str
    fn: Callable[[ActiveState], bool] = field(repr=False)

    def evaluate(self, state: ActiveState) -> bool:
        return self.fn(state)

    def __repr__(self) -> str:
        return f"custom({self.name})"


# ---------------------------------------------------------------------------
# Decision rules — with kinds, tags, exclusions (#8-#11)
# ---------------------------------------------------------------------------

class RuleKind(Enum):
    """#10: what a rule does when it fires."""
    BLOCK = "block"
    WARN = "warn"
    ROUTE = "route"
    HINT = "hint"


@dataclass
class DecisionRule:
    """A named propositional rule with kind, tags, and exclusion.

    #8: implication rules only emit action when antecedent is actually true.
    #9: kind separates facts (hint) from actions (route/block).
    #10: block/warn/route/hint consolidate behavior.
    #11: exclusive_with replaces hardcoded contradiction pairs.
    #21: risk_sensitive controls whether rule sees risk_level.
    """
    name: str
    condition: Prop
    action_if_true: str
    action_if_false: str = ""
    explanation: str = ""
    kind: RuleKind = RuleKind.ROUTE
    tags: list[str] = field(default_factory=list)
    exclusive_with: list[str] = field(default_factory=list)
    risk_sensitive: bool = False

    def evaluate(self, state: ActiveState) -> tuple[bool, str]:
        result = self.condition.evaluate(state)

        if result:
            # #8: suppress action on vacuous implication (antecedent false)
            if (
                self.kind in (RuleKind.HINT, RuleKind.WARN)
                and isinstance(self.condition, ImpliesProp)
                and not self.condition.antecedent.evaluate(state)
            ):
                return (True, "")
            return (True, self.action_if_true)

        if self.kind in (RuleKind.HINT, RuleKind.WARN) and not self.action_if_false:
            return (False, "")

        return (False, self.action_if_false)


# ---------------------------------------------------------------------------
# Logic layer — with tag filtering, scoped evaluation (#12-#13)
# ---------------------------------------------------------------------------

class LogicLayer:
    """Propositional logic glue with tag-scoped evaluation.

    #12: evaluate_for(tags=...) runs only matching rules.
    #13: rules organized by tags, not one flat pool.
    """

    def __init__(self) -> None:
        self.rules: list[DecisionRule] = []

    def add_rule(self, rule: DecisionRule) -> None:
        self.rules.append(rule)

    _risk_thresholds: dict[str, int] = {"low": 0, "normal": 1, "high": 2, "critical": 3}

    def _select_rules(
        self,
        tags: set[str] | None = None,
        risk_level: str = "normal",
    ) -> list[DecisionRule]:
        """#12: filter rules by tags. #21: skip risk_sensitive rules at low/normal risk."""
        elevated = self._risk_thresholds.get(risk_level, 1) >= 2
        rules = self.rules if tags is None else [
            r for r in self.rules
            if not r.tags or (set(r.tags) & tags)
        ]
        return [r for r in rules if not r.risk_sensitive or elevated]

    def evaluate_for(
        self,
        state: ActiveState,
        tags: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """#12: evaluate only rules matching tags."""
        results = []
        for rule in self._select_rules(tags, state.binding.risk_level):
            satisfied, action = rule.evaluate(state)
            results.append({
                "rule": rule.name,
                "kind": rule.kind.value,
                "condition": repr(rule.condition),
                "satisfied": satisfied,
                "action": action,
                "explanation": rule.explanation,
            })
        return results

    def evaluate_all(self, state: ActiveState) -> list[dict[str, Any]]:
        return self.evaluate_for(state, tags=None)

    def satisfied_actions(self, state: ActiveState, tags: set[str] | None = None) -> list[str]:
        rl = state.binding.risk_level
        return [
            action
            for rule in self._select_rules(tags, rl)
            for satisfied, action in [rule.evaluate(state)]
            if satisfied and action
        ]

    def unsatisfied_rules(self, state: ActiveState, tags: set[str] | None = None) -> list[str]:
        rl = state.binding.risk_level
        return [
            rule.name
            for rule in self._select_rules(tags, rl)
            if not rule.condition.evaluate(state)
        ]

    def consistency_check(self, state: ActiveState, tags: set[str] | None = None) -> dict[str, Any]:
        """#11: tag-based contradiction detection via exclusive_with."""
        rl = state.binding.risk_level
        results = self.evaluate_for(state, tags)
        active_actions = {r["action"] for r in results if r["satisfied"] and r["action"]}
        contradictions = []

        for rule in self._select_rules(tags, rl):
            satisfied, action = rule.evaluate(state)
            if satisfied and action and rule.exclusive_with:
                for ex in rule.exclusive_with:
                    if ex in active_actions:
                        contradictions.append(f"{action} contradicts {ex}")

        return {
            "consistent": len(contradictions) == 0,
            "contradictions": contradictions,
            "active_actions": sorted(active_actions),
        }

    def to_llm_context(self, state: ActiveState, tags: set[str] | None = None) -> dict[str, Any]:
        """Export logic evaluation as LLM context. #9: split by kind."""
        results = self.evaluate_for(state, tags)
        consistency = self.consistency_check(state, tags)

        facts = [r for r in results if r["kind"] in ("hint", "warn")]
        actions = [r for r in results if r["kind"] in ("route", "block")]

        return {
            "facts": facts,
            "actions": actions,
            "satisfied_actions": self.satisfied_actions(state, tags),
            "unsatisfied_rules": self.unsatisfied_rules(state, tags),
            "consistency": consistency,
        }


# ---------------------------------------------------------------------------
# Pre-built rule sets
# ---------------------------------------------------------------------------

def build_deploy_rules() -> LogicLayer:
    """Concrete deploy-decision rules demonstrating all 6 operators."""
    logic = LogicLayer()

    ev_tests = EvidencePresent("test_results")
    ev_approval = EvidencePresent("owner_approval")
    ev_rollback = EvidencePresent("rollback_plan")
    gate_deploy = GatePasses("deploy_gate")
    gate_blocked = GateBlocked("deploy_gate")
    role_analyst = RoleActive("analyst")
    role_approver = RoleActive("approver")
    has_gaps = HasMissingEvidence()
    high_risk = RiskAbove("high")
    ready = InState("ready_for_decision")
    t_deploy = TransitionAvailable("ready_to_deploy")

    logic.add_rule(DecisionRule(
        name="deploy_readiness",
        condition=ev_tests.AND(ev_approval).AND(gate_deploy),
        action_if_true="proceed_to_deploy",
        action_if_false="not_ready",
        kind=RuleKind.ROUTE,
        tags=["deploy", "readiness"],
        exclusive_with=["block_transition"],
    ))

    logic.add_rule(DecisionRule(
        name="gate_blocked_implies_collect",
        condition=gate_blocked.IMPLIES(has_gaps),
        action_if_true="collect_evidence",
        kind=RuleKind.HINT,
        tags=["deploy", "evidence"],
    ))

    logic.add_rule(DecisionRule(
        name="evidence_gap_detected",
        condition=ev_approval.NOT(),
        action_if_true="request_approval",
        kind=RuleKind.WARN,
        tags=["deploy", "evidence"],
    ))

    logic.add_rule(DecisionRule(
        name="role_separation",
        condition=role_analyst.XOR(role_approver),
        action_if_true="valid_role_assignment",
        action_if_false="role_conflict",
        kind=RuleKind.BLOCK,
        tags=["roles"],
    ))

    logic.add_rule(DecisionRule(
        name="recovery_path_exists",
        condition=ev_rollback.OR(t_deploy.NOT()),
        action_if_true="safe_to_proceed",
        action_if_false="no_safety_net",
        kind=RuleKind.WARN,
        tags=["deploy", "safety"],
    ))

    logic.add_rule(DecisionRule(
        name="readiness_equivalence",
        condition=ready.IFF(gate_deploy),
        action_if_true="state_gate_aligned",
        action_if_false="state_gate_mismatch",
        kind=RuleKind.HINT,
        tags=["deploy", "readiness"],
    ))

    logic.add_rule(DecisionRule(
        name="risk_escalation",
        condition=high_risk.AND(has_gaps).IMPLIES(
            CustomProp("should_escalate", lambda s: True)
        ),
        action_if_true="escalate_if_risky",
        kind=RuleKind.ROUTE,
        tags=["deploy", "risk"],
        risk_sensitive=True,
    ))

    return logic
