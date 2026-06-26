"""Example: "Should we deploy?" — walked through the FPF thinking map.

Demonstrates the full agentic run:
1. Load compiled primitives (build semantic map)
2. Bind inputs to variables
3. Construct active state
4. LLM reasons over the active map
5. Deterministic checks validate
6. Agent chooses outcome
"""

import json

from fpf_thinking_map.primitives import (
    ContextPrimitive,
    ContextBridge,
    RolePrimitive,
    AgencyLevel,
    CommitmentPrimitive,
    DeonticModality,
    GatePrimitive,
    GateCheck,
    EvidencePrimitive,
    FGR,
    Freshness,
    SemanticFloor,
    TransitionPrimitive,
    PublicationPrimitive,
    PublicationFace,
)
from fpf_thinking_map.state import SemanticMap, RuntimeBinding
from fpf_thinking_map.traversal import ThinkingMapTraversal


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
        if outcome.kind.value in (
            "abstain", "ask", "escalate", "publish",
            "collect_evidence", "idle", "bridge",
        ):
            break
        transitions = state.possible_transitions
        if transitions:
            t_out = engine.attempt_transition(state, transitions[0].transition_id)
            outcomes.append(t_out)
            if t_out.kind.value != "continue":
                break
        else:
            break

    for i, o in enumerate(outcomes):
        print(f"\n  Step {i + 1}: {o.kind.value} — {o.reason}")


if __name__ == "__main__":
    run_scenario_missing_evidence()
    run_scenario_role_conflict()
    run_scenario_full_traversal()
