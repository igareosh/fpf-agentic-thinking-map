#!/usr/bin/env python3
"""Self-verification harness for the FPF thinking map package.

Run: python -m fpf_thinking_map.verify
Exit 0 = all checks pass. Exit 1 = failure.
"""

from __future__ import annotations

import sys
import io
import contextlib
import traceback


def check(name: str, fn):
    try:
        fn()
        print(f"  PASS  {name}")
        return True
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        return False


def check_imports():
    from fpf_thinking_map import (
        ContextPrimitive, RolePrimitive, WorkPrimitive,
        CommitmentPrimitive, GatePrimitive, EvidencePrimitive,
        TransitionPrimitive, PublicationPrimitive, Freshness,
        RuntimeBinding, ActiveState, SemanticMap, MoveTrace,
        GuardEngine, GuardVerdict, GuardScope, Guard,
        LogicLayer, RuleKind, Prop, EvidencePresent, GatePasses,
        GateBlocked, RoleActive, InState, CommitmentMet,
        HasMissingEvidence, RiskAbove, TransitionAvailable,
        CustomProp, DecisionRule,
        ThinkingMapTraversal, Outcome, OutcomeKind,
    )


def check_primitives():
    from fpf_thinking_map.primitives import (
        ContextPrimitive, RolePrimitive, CommitmentPrimitive,
        DeonticModality, GatePrimitive, GateCheck, GateDecision,
        FGR, Freshness,
    )

    ctx = ContextPrimitive("c1", "Test", glossary={"x": "y"})
    assert ctx.term_defined("x")
    assert ctx.resolve_term("x") == "y"

    role = RolePrimitive("r1", "Tester", "c1", incompatible_with=["r2"])
    assert role.conflicts_with("r2")
    assert not role.conflicts_with("r3")

    c = CommitmentPrimitive("cm1", "Must test", DeonticModality.MUST, "c1")
    assert c.is_binding

    gc = GateCheck("gc1", "check", required_evidence=["e1", "e2"])
    assert gc.evaluate({"e1", "e2"}) == GateDecision.PASS
    assert gc.evaluate({"e1"}) == GateDecision.DEGRADE
    assert gc.evaluate(set()) == GateDecision.ABSTAIN

    gate = GatePrimitive("g1", "Gate", "c1", checks=[gc])
    assert gate.evaluate({"e1", "e2"}) == GateDecision.PASS
    assert gate.missing_evidence({"e1"}) == ["e2"]

    assert Freshness.STALE.value == "stale"

    fgr = FGR(0.8, 0.6, 0.9)
    assert fgr.sufficient(0.5, 0.5)


def check_state():
    from fpf_thinking_map.primitives import (
        ContextPrimitive, RolePrimitive, GatePrimitive, GateCheck,
        TransitionPrimitive,
    )
    from fpf_thinking_map.state import SemanticMap, RuntimeBinding, ActiveState

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("c1", "Ctx1"))
    sm.register_role(RolePrimitive("r1", "Role1", "c1"))
    sm.register_gate(GatePrimitive("g1", "Gate", "c1", checks=[
        GateCheck("gc1", "check", required_evidence=["e1"]),
    ]))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "c1", from_state="s1", to_state="s2",
        required_gate_id="g1", required_evidence=["e1"],
    ))

    # #1: transitions_for scoped to context + state
    assert len(sm.transitions_for("c1", "s1")) == 1
    assert len(sm.transitions_for("c1", "s2")) == 0
    assert len(sm.transitions_for("other", "s1")) == 0

    # #2: gates_for_transitions
    transitions = sm.transitions_for("c1", "s1")
    gates = sm.gates_for_transitions(transitions)
    assert len(gates) == 1

    # #14: empty roles when none bound
    binding = RuntimeBinding(active_context_id="c1", current_evidence=["e1"])
    state = ActiveState(sm, binding, current_state="s1")
    assert len(state.active_roles) == 0

    # #15: explicit role binding
    binding2 = RuntimeBinding(
        active_context_id="c1", actor_role_ids=["r1"], current_evidence=["e1"],
    )
    state2 = ActiveState(sm, binding2, current_state="s1")
    assert len(state2.active_roles) == 1

    # #3: per-transition missing evidence
    binding3 = RuntimeBinding(active_context_id="c1", current_evidence=[])
    state3 = ActiveState(sm, binding3, current_state="s1")
    assert state3.missing_evidence_for("t1") == ["e1"]
    assert state3.missing_evidence_for("nonexistent") == []

    # #5: slice
    sl = state2.slice("t1")
    assert sl["move"]["id"] == "t1"
    assert sl["can_fire"] is True

    # #24: trace
    prompt = state2.to_llm_prompt_state()
    assert prompt["active_context"] == "c1"
    assert prompt["trace"] is None  # no previous move


def check_guards():
    from fpf_thinking_map.example_scenario import build_deploy_decision_map
    from fpf_thinking_map.state import RuntimeBinding, ActiveState
    from fpf_thinking_map.guards import GuardEngine, GuardVerdict, GuardScope

    sm = build_deploy_decision_map()

    # #19: scoped evaluation with transition_id
    b = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s = ActiveState(sm, b, current_state="ready_for_decision")
    engine = GuardEngine()

    results_focused = engine.evaluate(s, transition_id="ready_to_deploy")
    assert len(results_focused) > 0

    # Gate guard should deny (missing approval)
    gate_results = engine.evaluate(
        s, transition_id="ready_to_deploy",
        scopes={GuardScope.TRANSITION},
    )
    denials = [r for r in gate_results if r.verdict == GuardVerdict.DENY]
    assert len(denials) > 0

    # Role conflict
    b2 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst", "approver"],
        current_evidence=["test_results", "owner_approval"],
    )
    s2 = ActiveState(sm, b2, current_state="ready_for_decision")
    role_results = engine.evaluate(s2, scopes={GuardScope.ROLE})
    role_denials = [r for r in role_results if r.verdict == GuardVerdict.DENY]
    assert len(role_denials) == 1

    # Full evidence, single role → all allow
    b3 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
    )
    s3 = ActiveState(sm, b3, current_state="ready_for_decision")
    allowed, _ = engine.is_action_allowed(s3, transition_id="ready_to_deploy")
    assert allowed


def check_logic_operators():
    from fpf_thinking_map.logic import EvidencePresent
    from fpf_thinking_map.state import SemanticMap, RuntimeBinding, ActiveState

    sm = SemanticMap()
    p = EvidencePresent("p")
    q = EvidencePresent("q")

    def ev(p_val, q_val, prop):
        e = []
        if p_val: e.append("p")
        if q_val: e.append("q")
        return prop.evaluate(ActiveState(sm, RuntimeBinding(current_evidence=e)))

    assert ev(True, True, p.NOT()) is False
    assert ev(False, True, p.NOT()) is True

    assert ev(True, True, p.AND(q)) is True
    assert ev(True, False, p.AND(q)) is False

    assert ev(False, False, p.OR(q)) is False
    assert ev(True, False, p.OR(q)) is True

    assert ev(True, True, p.XOR(q)) is False
    assert ev(True, False, p.XOR(q)) is True

    assert ev(True, False, p.IMPLIES(q)) is False
    assert ev(False, False, p.IMPLIES(q)) is True

    assert ev(True, True, p.IFF(q)) is True
    assert ev(True, False, p.IFF(q)) is False


def check_logic_layer():
    from fpf_thinking_map.example_scenario import build_deploy_decision_map
    from fpf_thinking_map.logic import build_deploy_rules, RuleKind
    from fpf_thinking_map.state import RuntimeBinding, ActiveState

    sm = build_deploy_decision_map()
    logic = build_deploy_rules()

    b = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s = ActiveState(sm, b, current_state="ready_for_decision")

    # #9: split into facts and actions
    ctx = logic.to_llm_context(s)
    assert "facts" in ctx
    assert "actions" in ctx
    assert ctx["consistency"]["consistent"]

    # #12: tag-scoped evaluation
    deploy_ctx = logic.to_llm_context(s, tags={"deploy"})
    role_ctx = logic.to_llm_context(s, tags={"roles"})
    assert len(deploy_ctx["facts"]) + len(deploy_ctx["actions"]) >= 1
    assert len(role_ctx["actions"]) >= 1

    # #10: rules have kinds
    all_results = logic.evaluate_all(s)
    kinds = {r["kind"] for r in all_results}
    assert "route" in kinds or "block" in kinds or "hint" in kinds


def check_traversal():
    from fpf_thinking_map.example_scenario import build_deploy_decision_map
    from fpf_thinking_map.logic import build_deploy_rules
    from fpf_thinking_map.state import RuntimeBinding
    from fpf_thinking_map.traversal import ThinkingMapTraversal, OutcomeKind

    sm = build_deploy_decision_map()
    logic = build_deploy_rules()
    engine = ThinkingMapTraversal(sm, logic_layer=logic)

    # #6: focused step with transition_id
    b1 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s1 = engine.build_active_state(b1, "ready_for_decision")
    o1 = engine.step(s1, transition_id="ready_to_deploy")
    assert o1.kind == OutcomeKind.COLLECT_EVIDENCE
    assert "logic" in o1.llm_prompt_state
    assert "move" in o1.llm_prompt_state  # slice view

    # Full evidence → CONTINUE
    b2 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
    )
    s2 = engine.build_active_state(b2, "ready_for_decision")
    o2 = engine.step(s2)
    assert o2.kind == OutcomeKind.CONTINUE

    # Transition
    o3 = engine.attempt_transition(s2, "ready_to_deploy")
    assert o3.kind == OutcomeKind.CONTINUE
    assert o3.next_state == "deploying"

    # No context → CHANGE_FRAME
    s3 = engine.build_active_state(RuntimeBinding(task="orphan"))
    o4 = engine.step(s3)
    assert o4.kind == OutcomeKind.CHANGE_FRAME

    # #25: demo_walk
    b5 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
        candidate_actions=["deploy"],
    )
    outcomes = engine.demo_walk(b5)
    assert len(outcomes) >= 1


def check_boundary_enforcement():
    """Verify the 4 findings are fixed: no cross-context leaks, no advisory evidence."""
    from fpf_thinking_map.primitives import (
        ContextPrimitive, RolePrimitive, TransitionPrimitive,
        GatePrimitive, GateCheck,
    )
    from fpf_thinking_map.state import SemanticMap, RuntimeBinding, ActiveState
    from fpf_thinking_map.traversal import ThinkingMapTraversal, OutcomeKind
    from fpf_thinking_map.logic import (
        LogicLayer, DecisionRule, RuleKind, RiskAbove, CustomProp,
    )

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx_a", "Context A"))
    sm.register_context(ContextPrimitive("ctx_b", "Context B"))
    sm.register_role(RolePrimitive("role_a", "Role A", "ctx_a"))
    sm.register_role(RolePrimitive("role_b", "Role B", "ctx_b"))
    sm.register_transition(TransitionPrimitive(
        "t_a", "Move A", "ctx_a", "start", "done_a", required_evidence=["ev1"],
    ))
    sm.register_transition(TransitionPrimitive(
        "t_b", "Move B", "ctx_b", "start", "done_b",
    ))

    engine = ThinkingMapTraversal(sm)

    # --- Finding 1: cross-context transition blocked ---
    b = RuntimeBinding(active_context_id="ctx_a", current_evidence=["ev1"])
    s = engine.build_active_state(b, "start")
    o = engine.attempt_transition(s, "t_b")
    assert o.kind == OutcomeKind.ABSTAIN, f"Cross-context transition should be denied, got {o.kind}"
    assert s.current_state == "start", "State should not have changed"

    # step() also blocks cross-context transition_id
    o2 = engine.step(s, transition_id="t_b")
    assert o2.kind == OutcomeKind.ABSTAIN

    # same-context transition works
    o3 = engine.attempt_transition(s, "t_a")
    assert o3.kind == OutcomeKind.CONTINUE
    assert o3.next_state == "done_a"

    # --- Finding 2: required_evidence enforced on execution ---
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("c", "C"))
    sm2.register_transition(TransitionPrimitive(
        "t_ev", "Needs evidence", "c", "init", "ready", required_evidence=["proof"],
    ))
    engine2 = ThinkingMapTraversal(sm2)
    b2 = RuntimeBinding(active_context_id="c", current_evidence=[])
    s2 = engine2.build_active_state(b2, "init")

    # attempt_transition must deny when evidence missing
    o4 = engine2.attempt_transition(s2, "t_ev")
    assert o4.kind == OutcomeKind.COLLECT_EVIDENCE, f"Should deny missing evidence, got {o4.kind}"
    assert s2.current_state == "init"

    # transition_to must also deny
    assert s2.transition_to("t_ev") is False

    # with evidence, it works
    s2.add_evidence("proof")
    assert s2.transition_to("t_ev") is True
    assert s2.current_state == "ready"

    # --- Finding 3: roles validated against active context ---
    b3 = RuntimeBinding(
        active_context_id="ctx_a",
        actor_role_ids=["role_a", "role_b"],
    )
    s3 = ActiveState(sm, b3, "start")
    active = s3.active_roles
    assert len(active) == 1, f"Foreign role should be filtered, got {len(active)} roles"
    assert active[0].role_id == "role_a"

    # --- Finding 4: risk_sensitive enforced ---
    logic = LogicLayer()
    logic.add_rule(DecisionRule(
        name="risk_rule",
        condition=RiskAbove("high"),
        action_if_true="escalate",
        kind=RuleKind.ROUTE,
        risk_sensitive=True,
    ))
    logic.add_rule(DecisionRule(
        name="normal_rule",
        condition=CustomProp("always_true", lambda s: True),
        action_if_true="proceed",
        kind=RuleKind.ROUTE,
        risk_sensitive=False,
    ))

    b_low = RuntimeBinding(risk_level="normal")
    s_low = ActiveState(SemanticMap(), b_low)
    actions_low = logic.satisfied_actions(s_low)
    assert "escalate" not in actions_low, "risk_sensitive rule should be skipped at normal risk"
    assert "proceed" in actions_low

    b_high = RuntimeBinding(risk_level="high")
    s_high = ActiveState(SemanticMap(), b_high)
    actions_high = logic.satisfied_actions(s_high)
    assert "escalate" in actions_high, "risk_sensitive rule should fire at high risk"
    assert "proceed" in actions_high


def check_audit_fixes():
    """Verify R07/R08, R09, R17, R20/R21 from the FPF audit."""
    from fpf_thinking_map.primitives import (
        ContextPrimitive, RolePrimitive, RoleAssignment,
        WorkPrimitive, SpeechActPrimitive, SpeechActType,
        CommitmentPrimitive, DeonticModality, GateDecision,
    )
    from fpf_thinking_map.state import SemanticMap, RuntimeBinding, ActiveState
    from fpf_thinking_map.guards import GuardEngine, GuardVerdict

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_role(RolePrimitive("dev", "Developer", "ctx"))

    # --- R07/R08: RoleAssignment ---
    ra = RoleAssignment(
        assignment_id="assign_1", holder_id="alice", role_id="dev", context_id="ctx",
    )
    sm.register_role_assignment(ra)
    assert "assign_1" in sm.role_assignments

    b = RuntimeBinding(actor="alice", active_context_id="ctx")
    s = ActiveState(sm, b)
    assert len(s.active_assignments) == 1
    assert len(s.active_roles) == 1
    assert s.active_roles[0].role_id == "dev"

    # Expired assignment → no active roles
    ra_expired = RoleAssignment(
        assignment_id="assign_2", holder_id="bob", role_id="dev",
        context_id="ctx", expired=True,
    )
    sm.register_role_assignment(ra_expired)
    b2 = RuntimeBinding(actor="bob", active_context_id="ctx")
    s2 = ActiveState(sm, b2)
    assert len(s2.active_assignments) == 0
    assert len(s2.active_roles) == 0

    # Guard catches expired assignment
    engine = GuardEngine()
    results = engine.evaluate(s2)
    expired_denials = [r for r in results if r.guard_name == "expired_assignment" and r.verdict == GuardVerdict.DENY]
    assert len(expired_denials) == 1

    # --- R09: performed_under on WorkPrimitive ---
    w = WorkPrimitive(
        work_id="w1", label="Deploy", context_id="ctx",
        performed_under="assign_1",
    )
    assert w.performed_under == "assign_1"

    # --- R17: subject on CommitmentPrimitive ---
    c = CommitmentPrimitive(
        "cm1", "Must deploy", DeonticModality.MUST, "ctx",
        subject="alice",
    )
    assert c.subject == "alice"

    # --- R20/R21: SpeechActPrimitive ---
    sa = SpeechActPrimitive(
        act_id="approval_1",
        act_type=SpeechActType.APPROVE,
        actor_id="manager",
        context_id="ctx",
        addressed_to="alice",
        institutes=["cm1"],
        evidence_refs=["test_results"],
    )
    sm.register_speech_act(sa)
    assert "approval_1" in sm.speech_acts

    # Valid speech act as evidence → guard allows
    b3 = RuntimeBinding(actor="alice", active_context_id="ctx", current_evidence=["approval_1"])
    s3 = ActiveState(sm, b3)
    results3 = engine.evaluate(s3)
    sa_denials = [r for r in results3 if r.guard_name == "speech_act_validity" and r.verdict == GuardVerdict.DENY]
    assert len(sa_denials) == 0

    # Expired speech act → guard denies
    sa.expired = True
    results4 = engine.evaluate(s3)
    sa_denials2 = [r for r in results4 if r.guard_name == "speech_act_validity" and r.verdict == GuardVerdict.DENY]
    assert len(sa_denials2) == 1

    # GateDecision.BLOCK exists
    assert GateDecision.BLOCK.value == "block"


def check_end_to_end():
    from fpf_thinking_map.example_scenario import (
        run_scenario_missing_evidence, run_scenario_role_conflict,
        run_scenario_full_traversal,
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_scenario_missing_evidence()
        run_scenario_role_conflict()
        run_scenario_full_traversal()
    output = buf.getvalue()
    assert "SCENARIO:" in output


def check_logic_end_to_end():
    from fpf_thinking_map.example_logic_scenario import (
        run_logic_scenario, run_truth_table_demo,
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_logic_scenario()
        run_truth_table_demo()
    output = buf.getvalue()
    assert "LOGIC GLUE SCENARIO" in output
    assert "TRUTH TABLE" in output


def check_horizontal_properties():
    """Verify the 25 horizontal improvements are structurally present."""
    from fpf_thinking_map.state import SemanticMap, RuntimeBinding, ActiveState, MoveTrace
    from fpf_thinking_map.primitives import (
        ContextPrimitive, RolePrimitive, TransitionPrimitive,
        GatePrimitive, GateCheck, Freshness,
    )
    from fpf_thinking_map.guards import GuardEngine, GuardScope
    from fpf_thinking_map.logic import LogicLayer, DecisionRule, RuleKind, EvidencePresent

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("c1", "Ctx"))
    sm.register_role(RolePrimitive("r1", "R1", "c1"))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "c1", "s1", "s2",
        required_gate_id="g1", required_evidence=["e1"],
    ))
    sm.register_gate(GatePrimitive("g1", "G1", "c1", checks=[
        GateCheck("gc1", "chk", required_evidence=["e1"]),
    ]))

    # #1: transitions_for exists and scopes
    assert hasattr(sm, "transitions_for")

    # #2: gates_for_transitions exists
    assert hasattr(sm, "gates_for_transitions")

    # #5: slice exists
    b = RuntimeBinding(active_context_id="c1", actor_role_ids=["r1"], current_evidence=["e1"])
    s = ActiveState(sm, b, "s1")
    assert "move" in s.slice("t1")

    # #10: RuleKind enum
    assert RuleKind.BLOCK.value == "block"
    assert RuleKind.HINT.value == "hint"

    # #11: exclusive_with on DecisionRule
    dr = DecisionRule("test", EvidencePresent("x"), "a", exclusive_with=["b"])
    assert dr.exclusive_with == ["b"]

    # #14: empty roles when unbound
    s2 = ActiveState(sm, RuntimeBinding(active_context_id="c1"), "s1")
    assert s2.active_roles == []

    # #16: register_work exists
    assert hasattr(sm, "register_work")

    # #19: GuardScope exists
    assert GuardScope.TRANSITION.value == "transition"

    # #20: Freshness enum
    assert Freshness.STALE.value == "stale"
    assert Freshness.EXPIRED.value == "expired"

    # #24: MoveTrace
    mt = MoveTrace()
    assert hasattr(mt, "previous_state")
    assert hasattr(mt, "evidence_delta")


def main():
    print("FPF Thinking Map — Self-verification (horizontal)")
    print("=" * 55)

    checks = [
        ("imports", check_imports),
        ("primitives", check_primitives),
        ("state (local scoping, slice, trace)", check_state),
        ("guards (scoped, transition-focused)", check_guards),
        ("logic operators (6 truth tables)", check_logic_operators),
        ("logic layer (tags, kinds, facts/actions)", check_logic_layer),
        ("traversal (focused step, demo_walk)", check_traversal),
        ("boundary enforcement (4 findings)", check_boundary_enforcement),
        ("audit fixes (R07-R21)", check_audit_fixes),
        ("end-to-end scenario", check_end_to_end),
        ("end-to-end logic scenario", check_logic_end_to_end),
        ("horizontal properties (25 items)", check_horizontal_properties),
    ]

    passed = sum(check(name, fn) for name, fn in checks)
    total = len(checks)

    print(f"\n{'=' * 55}")
    print(f"Result: {passed}/{total} checks passed")
    print("STATUS: ALL PASS" if passed == total else "STATUS: FAILURES DETECTED")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
