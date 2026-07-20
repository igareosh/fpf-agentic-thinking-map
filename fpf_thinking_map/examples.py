"""Deploy decision scenarios — the thinking map in action.

Demonstrates 6 scenarios:

  1. Missing evidence    — gate blocks, evidence collected, retry succeeds
  2. Role conflict       — analyst ⊥ approver, guard denies
  3. Full traversal      — assessing → ready → deploying (demo walk)
  4. Destructive HITL    — delete is legal (evidence+gate pass), still
                           refused until a human authorizes it
  5. Logic glue          — all 6 operators at each step, freshness-aware rules
  6. Truth table         — 6 operators on two evidence atoms, 4 rows

Run all:   python -m fpf_thinking_map.examples
Run one:   from fpf_thinking_map.examples import run_scenario_missing_evidence
Build map: from fpf_thinking_map.examples import build_deploy_decision_map
"""

import json

from fpf_thinking_map.logic import (
    CustomProp,
    DecisionRule,
    EvidenceFresh,
    EvidencePresent,
    GateBlocked,
    GatePasses,
    HasMissingEvidence,
    InState,
    LogicLayer,
    RiskAbove,
    RoleActive,
    RuleKind,
    TransitionAvailable,
)
from fpf_thinking_map.primitives import (
    AgencyLevel,
    CommitmentPrimitive,
    ContextBridge,
    ContextPrimitive,
    DeonticModality,
    EvidencePrimitive,
    FGR,
    Freshness,
    GateCheck,
    GatePrimitive,
    PublicationFace,
    PublicationPrimitive,
    RolePrimitive,
    SemanticFloor,
    TransitionPrimitive,
)
from fpf_thinking_map.state import ActiveState, RuntimeBinding, SemanticMap
from fpf_thinking_map.traversal import OutcomeKind, ThinkingMapTraversal


def build_deploy_decision_map() -> SemanticMap:
    """Build a semantic map for a deployment decision scenario."""
    sm = SemanticMap()

    sm.register_context(ContextPrimitive(
        context_id="project_delivery",
        label="Project Delivery",
        glossary={
            "deploy": "push artefact to production environment",
            "release": "make version available to users",
            "rollback": "revert to previous known-good state",
        },
        invariants=[
            "no deploy without passing tests",
            "no deploy without owner approval",
        ],
        bridges_to=[
            ContextBridge(
                target_context_id="operations",
                mapping={"deploy": "release_to_prod"},
                translation_loss="ops uses 'release' where dev uses 'deploy'",
            ),
        ],
    ))

    sm.register_context(ContextPrimitive(
        context_id="operations",
        label="Operations",
        glossary={
            "release_to_prod": "deploy artefact to production",
            "incident": "unplanned service disruption",
        },
    ))

    sm.register_role(RolePrimitive(
        role_id="analyst",
        label="Analyst",
        context_id="project_delivery",
        agency_level=AgencyLevel.DELIBERATIVE,
        responsibilities=["assess readiness", "evaluate evidence", "recommend"],
        incompatible_with=["approver"],
    ))

    sm.register_role(RolePrimitive(
        role_id="approver",
        label="Approver",
        context_id="project_delivery",
        agency_level=AgencyLevel.DELIBERATIVE,
        responsibilities=["authorize deploy", "accept risk"],
        incompatible_with=["analyst"],
    ))

    sm.register_commitment(CommitmentPrimitive(
        commitment_id="no_deploy_without_evidence",
        label="No deployment without evidence",
        modality=DeonticModality.MUST,
        context_id="project_delivery",
        scope="all deployments",
        evidence_refs=["test_results", "owner_approval"],
    ))

    sm.register_commitment(CommitmentPrimitive(
        commitment_id="rollback_plan_required",
        label="Rollback plan must exist",
        modality=DeonticModality.SHOULD,
        context_id="project_delivery",
        scope="production deployments",
        evidence_refs=["rollback_plan"],
    ))

    sm.register_gate(GatePrimitive(
        gate_id="deploy_gate",
        label="Deployment Gate",
        context_id="project_delivery",
        checks=[
            GateCheck(
                check_id="tests_pass",
                description="All tests must pass",
                required_evidence=["test_results"],
            ),
            GateCheck(
                check_id="approval_obtained",
                description="Owner approval must be obtained",
                required_evidence=["owner_approval"],
            ),
        ],
        fail_closed=True,
    ))

    sm.register_evidence(EvidencePrimitive(
        evidence_id="test_results",
        label="Test Suite Results",
        context_id="project_delivery",
        claim="code changes pass all tests",
        source="CI pipeline",
        fgr=FGR(formality=0.8, scope=0.6, reliability=0.9),
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.EVIDENTIARY,
        supports=["no_deploy_without_evidence"],
    ))

    sm.register_evidence(EvidencePrimitive(
        evidence_id="owner_approval",
        label="Owner Approval",
        context_id="project_delivery",
        claim="owner authorizes deployment",
        source="approval gate / speech act",
        fgr=FGR(formality=0.9, scope=0.8, reliability=0.95),
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.EVIDENTIARY,
        supports=["no_deploy_without_evidence"],
    ))

    sm.register_evidence(EvidencePrimitive(
        evidence_id="rollback_plan",
        label="Rollback Plan",
        context_id="project_delivery",
        claim="rollback procedure exists and is tested",
        source="runbook",
        fgr=FGR(formality=0.7, scope=0.5, reliability=0.8),
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.EVIDENTIARY,
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="assess_to_ready",
        label="Assessment complete → Ready for decision",
        context_id="project_delivery",
        from_state="assessing",
        to_state="ready_for_decision",
        required_evidence=["test_results"],
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="ready_to_deploy",
        label="Ready → Deploy",
        context_id="project_delivery",
        from_state="ready_for_decision",
        to_state="deploying",
        required_gate_id="deploy_gate",
        required_evidence=["test_results", "owner_approval"],
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="ready_to_escalate",
        label="Ready → Escalate (insufficient evidence)",
        context_id="project_delivery",
        from_state="ready_for_decision",
        to_state="escalated",
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="ops_release",
        label="Release to production",
        context_id="operations",
        from_state="releasing",
        to_state="monitoring",
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="ops_monitor_stable",
        label="Monitor → Stable",
        context_id="operations",
        from_state="monitoring",
        to_state="stable",
    ))

    sm.register_publication(PublicationPrimitive(
        publication_id="deploy_assurance_view",
        label="Deployment Assurance View",
        context_id="project_delivery",
        face=PublicationFace.ASSURANCE,
        audience="stakeholders",
        source_work_ids=["deploy_assessment"],
        required_gate_id="deploy_gate",
    ))

    return sm


def run_scenario_missing_evidence():
    """Scenario: analyst tries to decide but evidence is missing."""
    print("=" * 60)
    print("SCENARIO: Deploy decision — missing owner approval")
    print("=" * 60)

    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm)

    binding = RuntimeBinding(
        task="decide whether to deploy v2.1.0",
        goal="deploy if safe, escalate if not",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        audience="team lead",
        active_context_id="project_delivery",
        current_evidence=["test_results"],
        risk_level="normal",
        candidate_actions=["collect_evidence", "check_gate", "publish_assurance_view", "escalate"],
        constraints=["no_commitment_without_evidence", "planning_not_equal_enactment"],
    )

    state = engine.build_active_state(binding, current_state="ready_for_decision")

    print("\n--- Active State (what the LLM sees) ---")
    print(json.dumps(state.to_llm_prompt_state(), indent=2))

    print("\n--- Step 1: LLM evaluates ---")
    outcome = engine.step(state)
    print(json.dumps(outcome.to_dict(), indent=2))

    print("\n--- Step 2: Try transition to deploy ---")
    t_outcome = engine.attempt_transition(state, "ready_to_deploy")
    print(json.dumps(t_outcome.to_dict(), indent=2))

    print("\n--- Step 3: Evidence collected, retry ---")
    state.add_evidence("owner_approval")
    outcome2 = engine.step(state)
    print(json.dumps(outcome2.to_dict(), indent=2))

    print("\n--- Step 4: Transition to deploy (with evidence) ---")
    t_outcome2 = engine.attempt_transition(state, "ready_to_deploy")
    print(json.dumps(t_outcome2.to_dict(), indent=2))

    print("\n--- Slice view for ready_to_deploy ---")
    state2 = engine.build_active_state(
        RuntimeBinding(
            actor_role_ids=["analyst"],
            active_context_id="project_delivery",
            current_evidence=["test_results", "owner_approval"],
        ),
        current_state="ready_for_decision",
    )
    print(json.dumps(state2.slice("ready_to_deploy"), indent=2))


def run_scenario_role_conflict():
    """Scenario: same actor tries to be analyst AND approver."""
    print("\n" + "=" * 60)
    print("SCENARIO: Role conflict — analyst cannot also approve")
    print("=" * 60)

    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm)

    binding = RuntimeBinding(
        task="approve own deployment",
        goal="self-approve and deploy",
        actor="Solo Dev",
        actor_role_ids=["analyst", "approver"],
        active_context_id="project_delivery",
        current_evidence=["test_results", "owner_approval"],
        candidate_actions=["approve", "deploy"],
    )

    state = engine.build_active_state(binding, current_state="ready_for_decision")

    from fpf_thinking_map.guards import GuardEngine
    engine_g = GuardEngine()
    print(f"\nActive roles: {[r.role_id for r in state.active_roles]}")
    results = engine_g.evaluate(state)
    for r in results:
        if r.verdict.value != "allow":
            print(f"  {r.verdict.value}: {r.reason}")


def run_scenario_full_traversal():
    """Scenario: demo walk from assessing to deploy."""
    print("\n" + "=" * 60)
    print("SCENARIO: Demo walk — from assessing to deploy")
    print("=" * 60)

    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm)

    binding = RuntimeBinding(
        task="assess and deploy v2.1.0",
        goal="deploy if all evidence present",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        active_context_id="project_delivery",
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
        candidate_actions=["assess", "deploy", "escalate"],
    )

    state = engine.build_active_state(binding, current_state="assessing")
    outcomes = []
    for _ in range(10):
        outcome = engine.step(state)
        outcomes.append(outcome)
        if outcome.kind in (
            OutcomeKind.ABSTAIN, OutcomeKind.ASK, OutcomeKind.ESCALATE,
            OutcomeKind.PUBLISH, OutcomeKind.COLLECT_EVIDENCE,
            OutcomeKind.IDLE, OutcomeKind.BRIDGE,
        ):
            break
        transitions = state.possible_transitions
        if transitions:
            t_out = engine.attempt_transition(state, transitions[0].transition_id)
            outcomes.append(t_out)
            if t_out.kind != OutcomeKind.CONTINUE:
                break
        else:
            break

    for i, o in enumerate(outcomes):
        print(f"\n  Step {i + 1}: {o.kind.value} — {o.reason}")


def build_destructive_action_map() -> SemanticMap:
    """A minimal map for one destructive move: delete.

    Evidence and gate are both satisfiable on their own terms — FPF
    legality alone would say the traversal is CONTINUE, same as any
    other move. requires_human_authorization is the separate HITL layer stacked on top:
    the model can see the delete is ready, it still can't fire it.
    """
    sm = SemanticMap()

    sm.register_context(ContextPrimitive(
        context_id="data_ops",
        label="Data Operations",
        invariants=["no delete without a clean dry-run"],
    ))

    sm.register_gate(GatePrimitive(
        gate_id="delete_gate",
        label="Delete Gate",
        context_id="data_ops",
        checks=[GateCheck(
            check_id="dry_run_clean",
            description="Dry-run reports no unintended targets",
            required_evidence=["dry_run_report"],
        )],
    ))

    sm.register_transition(TransitionPrimitive(
        transition_id="delete_records",
        label="Delete matching records",
        context_id="data_ops",
        from_state="reviewed",
        to_state="deleted",
        required_gate_id="delete_gate",
        required_evidence=["dry_run_report"],
        requires_human_authorization=True,
    ))

    return sm


def run_scenario_destructive_hitl():
    """Scenario: the model reasons a delete is legal — HITL still gates it.

    Evidence is present, the gate passes — the FPF logic layer alone
    would say CONTINUE, nothing structurally wrong with firing. This is
    exactly the case requires_human_authorization exists for: destructive/irreversible
    moves where legal should not silently become autonomous.
    """
    print("\n" + "=" * 60)
    print("SCENARIO: Destructive delete — legal, but HITL-gated")
    print("=" * 60)

    sm = build_destructive_action_map()
    engine = ThinkingMapTraversal(sm)

    binding = RuntimeBinding(
        task="clean up orphaned records",
        goal="delete records flagged by dry-run",
        actor="ops_agent",
        active_context_id="data_ops",
        current_evidence=["dry_run_report"],
    )
    state = engine.build_active_state(binding, current_state="reviewed")

    print("\n--- Slice view: evidence present, gate passing, still not fireable ---")
    print(json.dumps(state.slice("delete_records"), indent=2))

    print("\n--- Model attempts to fire it directly (no authorization) ---")
    outcome = engine.attempt_transition(state, "delete_records")
    print(json.dumps(outcome.to_dict(), indent=2))

    print("\n--- Human says yes — authorized=True from a human-only channel ---")
    outcome2 = engine.attempt_transition(state, "delete_records", authorized=True)
    print(json.dumps(outcome2.to_dict(), indent=2))


def build_deploy_rules() -> LogicLayer:
    """Deploy-decision rules demonstrating all 6 operators + freshness-aware checks.

    Domain-specific: uses the deploy scenario's evidence IDs, gate IDs, and roles.
    For your own domain, build a LogicLayer with your own DecisionRules.
    """
    logic = LogicLayer()

    ev_tests = EvidencePresent("test_results")
    ev_approval = EvidencePresent("owner_approval")
    ev_rollback = EvidencePresent("rollback_plan")
    ev_tests_fresh = EvidenceFresh("test_results")
    ev_approval_fresh = EvidenceFresh("owner_approval")
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
        condition=ev_tests_fresh.AND(ev_approval_fresh).AND(gate_deploy),
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
        name="evidence_decay_warning",
        condition=ev_tests.AND(ev_tests_fresh.NOT()),
        action_if_true="evidence_stale_refresh_needed",
        kind=RuleKind.WARN,
        tags=["deploy", "evidence", "decay"],
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


def run_logic_scenario():
    """Deploy decision with logic glue — step by step."""
    print("=" * 70)
    print("LOGIC GLUE SCENARIO: Deploy decision with all 6 operators")
    print("=" * 70)

    sm = build_deploy_decision_map()
    logic = build_deploy_rules()
    engine = ThinkingMapTraversal(sm, logic_layer=logic)

    print("\n--- STEP 1: Analyst, missing approval ---")
    binding = RuntimeBinding(
        task="decide whether to deploy v2.1.0",
        goal="deploy if safe",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        active_context_id="project_delivery",
        current_evidence=["test_results"],
        risk_level="normal",
        candidate_actions=["collect_evidence", "escalate", "deploy"],
    )

    state = engine.build_active_state(binding, current_state="ready_for_decision")
    logic_eval = logic.to_llm_context(state)

    print("\nFacts:")
    for r in logic_eval["facts"]:
        mark = "✓" if r["satisfied"] else "✗"
        print(f"  {mark} {r['rule']}: {r['condition']} → {r['action']}")
    print("\nActions:")
    for r in logic_eval["actions"]:
        mark = "✓" if r["satisfied"] else "✗"
        print(f"  {mark} {r['rule']}: {r['condition']} → {r['action']}")

    print(f"\nSatisfied actions: {logic_eval['satisfied_actions']}")
    print(f"Consistency: {logic_eval['consistency']['consistent']}")

    # Focused step on the deploy transition
    outcome = engine.step(state, transition_id="ready_to_deploy", logic_tags={"deploy"})
    print(f"\nFocused step (ready_to_deploy): {outcome.kind.value} — {outcome.reason}")

    print("\n--- STEP 2: Approval obtained ---")
    state.add_evidence("owner_approval")
    logic_eval2 = logic.to_llm_context(state, tags={"deploy"})
    print(f"Satisfied (deploy tags): {logic_eval2['satisfied_actions']}")

    print("\n--- STEP 3: Full evidence ---")
    state.add_evidence("rollback_plan")
    outcome3 = engine.step(state, transition_id="ready_to_deploy")
    print(f"Step: {outcome3.kind.value} — {outcome3.reason}")

    print("\n--- STEP 4: Role conflict ---")
    state.binding.actor_role_ids = ["analyst", "approver"]
    logic_eval4 = logic.to_llm_context(state, tags={"roles"})
    for r in logic_eval4["actions"]:
        print(f"  {r['rule']}: satisfied={r['satisfied']} → {r['action']}")

    print("\n--- STEP 5: High risk + gaps ---")
    state.binding.risk_level = "high"
    state.binding.current_evidence = ["test_results"]
    state.binding.actor_role_ids = ["analyst"]
    logic_eval5 = logic.to_llm_context(state, tags={"risk"})
    for r in logic_eval5["actions"]:
        print(f"  {r['rule']}: satisfied={r['satisfied']} → {r['action']}")


def run_truth_table_demo():
    """Show truth table behavior of the 6 operators."""
    print("\n" + "=" * 70)
    print("TRUTH TABLE: 6 operators on two evidence atoms")
    print("=" * 70)

    sm = SemanticMap()
    p = EvidencePresent("p")
    q = EvidencePresent("q")

    ops = [
        ("¬p (NOT)", p.NOT()),
        ("p ∧ q (AND)", p.AND(q)),
        ("p ∨ q (OR)", p.OR(q)),
        ("p ⊕ q (XOR)", p.XOR(q)),
        ("p → q (IMPLIES)", p.IMPLIES(q)),
        ("p ↔ q (IFF)", p.IFF(q)),
    ]

    header = f"{'p':>5} {'q':>5} | " + " | ".join(f"{name:>16}" for name, _ in ops)
    print(f"\n{header}")
    print("-" * len(header))

    for p_val, q_val in [(True, True), (True, False), (False, True), (False, False)]:
        evidence = []
        if p_val:
            evidence.append("p")
        if q_val:
            evidence.append("q")

        binding = RuntimeBinding(current_evidence=evidence)
        state = ActiveState(semantic_map=sm, binding=binding)

        values = ["A" if op.evaluate(state) else "F" for _, op in ops]

        row = f"{'A' if p_val else 'F':>5} {'A' if q_val else 'F':>5} | "
        row += " | ".join(f"{v:>16}" for v in values)
        print(row)


if __name__ == "__main__":
    run_scenario_missing_evidence()
    run_scenario_role_conflict()
    run_scenario_full_traversal()
    run_scenario_destructive_hitl()
    run_logic_scenario()
    run_truth_table_demo()
