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

from dev_mcp.server import get_audit_gaps, get_fpf_source_mapping, run_scenario, run_verify


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


def main() -> int:
    print("dev_mcp — self-test")
    print("=" * 55)

    checks = [
        ("get_fpf_source_mapping content", check_source_mapping),
        ("get_audit_gaps unfiltered", check_audit_gaps_unfiltered),
        ("get_audit_gaps filtered", check_audit_gaps_filtered),
        ("get_audit_gaps no-match message", check_audit_gaps_no_match),
        ("run_scenario: valid scope=core", check_run_scenario_valid_core),
        ("run_scenario: valid scope=user-extension", check_run_scenario_valid_user_extension),
        ("run_scenario: invalid scope rejected", check_run_scenario_invalid_scope_rejected),
        ("run_scenario: exception path", check_run_scenario_exception_path),
        ("run_scenario: no `result` assigned", check_run_scenario_no_result_assigned),
        ("run_scenario: stdout capture", check_run_scenario_stdout_capture),
        ("run_scenario: real engine construction", check_run_scenario_engine_construction),
        ("run_verify: underlying harness passes", check_run_verify_passes),
    ]

    passed = sum(check(name, fn) for name, fn in checks)
    total = len(checks)

    print(f"\n{'=' * 55}")
    print(f"Result: {passed}/{total} checks passed")
    print("STATUS: ALL PASS" if passed == total else "STATUS: FAILURES DETECTED")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
