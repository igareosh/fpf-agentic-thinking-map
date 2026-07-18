"""dev_mcp self-test — same check()/PASS-FAIL style as fpf_thinking_map/verify.py.

Not pytest: this repo tests itself with plain asserts + a runner, on purpose
(zero test-framework dependency, matches the library's own "no dependencies"
discipline). dev_mcp being a dev-only tool doesn't mean it's untested — a
canonical test surface that's never been tested itself is a contradiction.

Run: python -m dev_mcp.test_server  (from repo root, fpf_thinking_map
installed — `pip install -e .` first)
"""

from __future__ import annotations

import json
import sys
import traceback

from dev_mcp.server import (
    get_advisories,
    get_advisory_log,
    get_audit_gaps,
    get_fpf_source_mapping,
    run_scenario,
    run_verify,
)


def check(name: str, fn) -> bool:
    try:
        fn()
        print(f"  PASS  {name}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        return False


def check_source_mapping():
    text = get_fpf_source_mapping()
    assert "ContextPrimitive" in text, "expected primitive names in SOURCES.md content"
    assert "A.1.1" in text, "expected an FPF spec section ID"


def check_audit_gaps_unfiltered():
    text = get_audit_gaps()
    assert "R01" in text and "R50" in text, "expected the full R01-R50 backlog unfiltered"


def check_audit_gaps_filtered():
    text = get_audit_gaps("missing")
    lines = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
    assert lines, "expected at least one filtered row"
    # every data row (skip the header/separator rows) must actually contain "missing"
    data_rows = [ln for ln in lines if not ln.strip().startswith("| ID") and "---" not in ln]
    assert data_rows, "expected filtered data rows, not just header"
    assert all("missing" in ln.lower() for ln in data_rows), "filter leaked non-matching rows"


def check_audit_gaps_no_match():
    text = get_audit_gaps("zzz-no-such-status-exists")
    assert text.startswith("(no rows matching"), f"expected the no-match message, got: {text[:80]}"


def check_advisories_content():
    text = get_advisories()
    for adv_id in ("ADV-01", "ADV-02", "ADV-03", "ADV-04", "ADV-05", "ADV-06", "ADV-07", "ADV-08"):
        assert adv_id in text, f"expected {adv_id} present"
    assert "Not defects" in text, "advisories must be framed as advisories, not bugs"


def check_run_scenario_valid_core():
    out = json.loads(run_scenario("result = 1 + 1", scope="core"))
    assert out["scope"] == "core"
    assert out["result"] == "2"


def check_run_scenario_valid_user_extension():
    out = json.loads(run_scenario("result = 'ok'", scope="user-extension"))
    assert out["scope"] == "user-extension"
    assert out["result"] == "'ok'"


def check_run_scenario_invalid_scope_rejected():
    out = json.loads(run_scenario("result = 1", scope="not-a-real-scope"))
    assert "error" in out, "invalid scope must be rejected before any code executes"
    assert "not-a-real-scope" in out["error"], "error message should name the bad value"


def check_run_scenario_exception_path():
    out = json.loads(run_scenario("result = 1 / 0", scope="core"))
    assert out["scope"] == "core"
    assert "ZeroDivisionError" in out["error"]


def check_run_scenario_no_result_assigned():
    out = json.loads(run_scenario("x = 1  # never assigns `result`", scope="core"))
    assert "no `result` assigned" in out["result"]


def check_run_scenario_stdout_capture():
    out = json.loads(run_scenario("print('hello from scenario'); result = None", scope="core"))
    assert "hello from scenario" in out["stdout"]


def check_run_scenario_engine_construction():
    """The real end-to-end path: build a SemanticMap, step the engine, get a real outcome."""
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_transition(TransitionPrimitive("t1", "Go", "ctx", "start", "done"))
engine = ThinkingMapTraversal(sm)
s = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="start")
outcome = engine.step(s)
result = outcome.kind.value
"""
    out = json.loads(run_scenario(code, scope="core"))
    assert out["result"] == "'continue'", out


def check_run_verify_passes():
    out = run_verify()
    assert "STATUS: ALL PASS" in out, f"expected the underlying verify harness to pass, got: {out[-200:]}"


# ── Advisory-trigger awareness (not a fix, not enforcement — see advisory_detectors.py) ──


def _triggered_ids(out: dict) -> set[str]:
    return {h["advisory"] for h in out.get("advisories_triggered", [])}


def check_run_scenario_no_advisories_on_trivial_code():
    """Negative control: code that never touches an ActiveState must not carry the key at all."""
    out = json.loads(run_scenario("result = 1 + 1", scope="core"))
    assert "advisories_triggered" not in out, "trivial scenario with no ActiveState must not trigger anything"


def check_adv01_evidence_staleness_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_evidence(EvidencePrimitive("ev1", "Evidence 1", "ctx", ttl_steps=1))
sm.register_transition(TransitionPrimitive("t1", "Go", "ctx", "start", "done", required_evidence=["ev1"]))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", current_evidence=["ev1"]), current_state="start"
)
state.step_count = 5  # age 5 >= ttl(1) * 2 -> EXPIRED
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-01" in ids, f"expected ADV-01, got {ids} — full: {out}"


def check_adv02_risk_not_filtering_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_transition(TransitionPrimitive("t1", "Go", "ctx", "start", "done"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", risk_level="critical"), current_state="start"
)
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-02" in ids, f"expected ADV-02, got {ids} — full: {out}"


def check_adv03_context_self_asserted_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="start")
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-03" in ids, f"expected ADV-03, got {ids} — full: {out}"


def check_adv04_contradiction_opt_in_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
layer = LogicLayer()
layer.add_rule(DecisionRule(name="r_proceed", condition=InState("start"), action_if_true="proceed"))
layer.add_rule(DecisionRule(name="r_hold", condition=InState("start"), action_if_true="hold"))
engine = ThinkingMapTraversal(sm, logic_layer=layer)
state = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="start")
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-04" in ids, f"expected ADV-04, got {ids} — full: {out}"


def check_adv04_no_false_positive_when_declared_exclusive():
    """Same two opposite-action rules, but exclusive_with declared both ways -> not a fresh ADV-04 hit."""
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
layer = LogicLayer()
layer.add_rule(DecisionRule(
    name="r_proceed", condition=InState("start"), action_if_true="proceed", exclusive_with=["hold"],
))
layer.add_rule(DecisionRule(
    name="r_hold", condition=InState("start"), action_if_true="hold", exclusive_with=["proceed"],
))
engine = ThinkingMapTraversal(sm, logic_layer=layer)
state = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="start")
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-04" not in ids, f"exclusive_with was declared both ways, ADV-04 should not fire — full: {out}"


def check_adv05_degrade_granularity_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_gate(GatePrimitive("g1", "Gate 1", "ctx", checks=[
    GateCheck("c1", "Check 1", required_evidence=["e1"]),
    GateCheck("c2", "Check 2", required_evidence=["e2"]),
]))
sm.register_transition(TransitionPrimitive("t1", "Go", "ctx", "start", "done", required_gate_id="g1"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", current_evidence=["e1"]), current_state="start"
)
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-05" in ids, f"expected ADV-05, got {ids} — full: {out}"


def check_adv06_agency_not_enforced_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_role(RolePrimitive("r1", "Role 1", "ctx", agency_level=AgencyLevel.PASSIVE))
sm.register_transition(TransitionPrimitive("t1", "Go", "ctx", "start", "done"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", actor_role_ids=["r1"]), current_state="start"
)
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-06" in ids, f"expected ADV-06, got {ids} — full: {out}"


def check_adv07_risk_case_sensitivity_detected():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", risk_level="CRITICAL"), current_state="start"
)
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-07" in ids, f"expected ADV-07 (bad-case risk_level), got {ids} — full: {out}"


def check_adv07_no_false_positive_on_correct_case():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", risk_level="critical"), current_state="start"
)
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-07" not in ids, f"correctly-cased risk_level must not trigger ADV-07 — full: {out}"


def check_adv08_no_persistence_surface_always_noted():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="start")
result = "ok"
"""
    out = json.loads(run_scenario(code, scope="core"))
    ids = _triggered_ids(out)
    assert "ADV-08" in ids, f"expected ADV-08 (standing fact, every ActiveState), got {ids} — full: {out}"


def check_advisory_log_persists_across_calls():
    code = """
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(active_context_id="ctx", risk_level="NOT-A-REAL-LEVEL"), current_state="start"
)
result = "ok"
"""
    run_scenario(code, scope="core")
    out = json.loads(get_advisory_log(limit=5))
    assert out["total_logged"] >= 1, f"expected at least one logged entry, got: {out}"
    assert out["entries"], "expected entries to come back non-empty"
    most_recent = out["entries"][0]
    assert "ADV-07" in most_recent["advisories"], f"expected the just-triggered ADV-07 at the top: {most_recent}"


def main() -> int:
    print("dev_mcp — self-test")
    print("=" * 55)

    checks = [
        ("get_fpf_source_mapping content", check_source_mapping),
        ("get_audit_gaps unfiltered", check_audit_gaps_unfiltered),
        ("get_audit_gaps filtered", check_audit_gaps_filtered),
        ("get_audit_gaps no-match message", check_audit_gaps_no_match),
        ("get_advisories content", check_advisories_content),
        ("run_scenario: valid scope=core", check_run_scenario_valid_core),
        ("run_scenario: valid scope=user-extension", check_run_scenario_valid_user_extension),
        ("run_scenario: invalid scope rejected", check_run_scenario_invalid_scope_rejected),
        ("run_scenario: exception path", check_run_scenario_exception_path),
        ("run_scenario: no `result` assigned", check_run_scenario_no_result_assigned),
        ("run_scenario: stdout capture", check_run_scenario_stdout_capture),
        ("run_scenario: real engine construction", check_run_scenario_engine_construction),
        ("run_verify: underlying harness passes", check_run_verify_passes),
        ("advisories: no trigger on trivial code", check_run_scenario_no_advisories_on_trivial_code),
        ("advisories: ADV-01 evidence staleness detected", check_adv01_evidence_staleness_detected),
        ("advisories: ADV-02 risk not filtering detected", check_adv02_risk_not_filtering_detected),
        ("advisories: ADV-03 context self-asserted detected", check_adv03_context_self_asserted_detected),
        ("advisories: ADV-04 contradiction opt-in detected", check_adv04_contradiction_opt_in_detected),
        ("advisories: ADV-04 no false positive when declared exclusive", check_adv04_no_false_positive_when_declared_exclusive),
        ("advisories: ADV-05 DEGRADE granularity detected", check_adv05_degrade_granularity_detected),
        ("advisories: ADV-06 agency not enforced detected", check_adv06_agency_not_enforced_detected),
        ("advisories: ADV-07 risk case sensitivity detected", check_adv07_risk_case_sensitivity_detected),
        ("advisories: ADV-07 no false positive on correct case", check_adv07_no_false_positive_on_correct_case),
        ("advisories: ADV-08 no persistence surface always noted", check_adv08_no_persistence_surface_always_noted),
        ("advisories: log persists across calls", check_advisory_log_persists_across_calls),
    ]

    passed = sum(check(name, fn) for name, fn in checks)
    total = len(checks)

    print(f"\n{'=' * 55}")
    print(f"Result: {passed}/{total} checks passed")
    print("STATUS: ALL PASS" if passed == total else "STATUS: FAILURES DETECTED")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
