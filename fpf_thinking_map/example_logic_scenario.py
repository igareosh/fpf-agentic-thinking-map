"""Example: Logic glue layer in action — all 6 operators at each step.

Shows how propositional logic (NOT, AND, OR, XOR, IMPLIES, IFF)
provides deterministic decision glue between FPF semantic primitives
and the LLM's reasoning.
"""

import json

from fpf_thinking_map.example_scenario import build_deploy_decision_map
from fpf_thinking_map.logic import build_deploy_rules
from fpf_thinking_map.state import RuntimeBinding
from fpf_thinking_map.traversal import ThinkingMapTraversal


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
        actor="Felix",
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

    from fpf_thinking_map.logic import EvidencePresent
    from fpf_thinking_map.state import SemanticMap, ActiveState, RuntimeBinding

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
    run_logic_scenario()
    run_truth_table_demo()
