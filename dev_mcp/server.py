"""dev_mcp server for agentic testing of fpf_thinking_map.

Agent-first summary:
- Run scenarios quickly: run_scenario(code, scope)
- Run shipped verification: run_verify()
- Read deep docs when needed: sources, gap audit, advisories
- Every run_scenario call is checked against all 8 ADVISORIES.md conditions;
  hits ride along in the response and get appended to a durable log —
  inspect it later with get_advisory_log(). This is awareness, not
  enforcement: nothing here blocks or fixes anything, see advisory_detectors.py.

scope is required on run_scenario:
- core: testing shipped library behavior
- user-extension: testing downstream maps built on top
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from dev_mcp.advisory_detectors import detect_advisories, find_active_states_and_logic

mcp = FastMCP("fpf-thinking-map-test")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEEP_DOCS = REPO_ROOT / "docs" / "deep"
SOURCES_MD = DEEP_DOCS / "SOURCES.md"
AUDIT_MD = DEEP_DOCS / "FPF_SOURCE_TO_CODE_RELATION_AUDIT.md"
ADVISORIES_MD = DEEP_DOCS / "ADVISORIES.md"

STATE_DIR = REPO_ROOT / "dev_mcp" / ".state"
ADVISORY_LOG = STATE_DIR / "advisory_log.jsonl"


_VALID_SCOPES = {"core", "user-extension"}


def _run_advisory_detection(ns: dict, scope: str, code: str) -> list[dict[str, str]]:
    """Best-effort: scan the scenario's namespace, run all 8 detectors, log hits.

    Never raises — a detector bug must not break run_scenario's actual job.
    """
    try:
        hits: list[dict[str, str]] = []
        for var_name, state, logic_layer in find_active_states_and_logic(ns):
            for hit in detect_advisories(state, logic_layer):
                d = hit.to_dict()
                d["variable"] = var_name
                hits.append(d)

        if hits:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "scope": scope,
                "advisories": sorted({h["advisory"] for h in hits}),
                "hits": hits,
                "code_excerpt": code[:200],
            }
            with ADVISORY_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")

        return hits
    except Exception as exc:  # noqa: BLE001 — awareness layer, must never break the real tool
        return [{"advisory": "ADV-DETECT-ERROR", "title": "advisory detection failed", "tier": "internal",
                  "detail": f"{type(exc).__name__}: {exc}"}]


@mcp.tool(
    description=(
        "Run Python scenario code with fpf_thinking_map classes pre-imported. "
        "Assign to `result` to return output. "
        "scope is required: core (library behavior) or user-extension (downstream map behavior)."
    )
)
def run_scenario(code: str, scope: str) -> str:
    if scope not in _VALID_SCOPES:
        return json.dumps(
            {"error": f"scope must be one of {sorted(_VALID_SCOPES)}, got {scope!r}"},
            indent=2,
        )

    ns: dict = {}
    try:
        exec("from fpf_thinking_map import *", ns)  # noqa: S102 — local dev tool, not a security boundary
        exec("from fpf_thinking_map.traversal import ThinkingMapTraversal, Outcome, OutcomeKind", ns)
        exec("from fpf_thinking_map.guards import GuardEngine, GuardVerdict, GuardScope", ns)
        exec("from fpf_thinking_map.logic import LogicLayer, DecisionRule, RuleKind, EvidenceFresh", ns)
    except ImportError as exc:
        return json.dumps(
            {
                "scope": scope,
                "error": f"fpf_thinking_map is not importable: {exc}. "
                         f"Run `pip install -e .` from the repo root first.",
            },
            indent=2,
        )

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)  # noqa: S102 — see docstring
    except Exception as exc:  # noqa: BLE001 — reporting the failure IS the point of this tool
        # A scenario can build real state before hitting an unrelated error later —
        # still worth checking what was built, so a failed scenario doesn't also
        # silently lose whatever advisory awareness it already earned.
        advisories_triggered = _run_advisory_detection(ns, scope, code)
        payload = {"scope": scope, "error": f"{type(exc).__name__}: {exc}", "stdout": buf.getvalue()}
        if advisories_triggered:
            payload["advisories_triggered"] = advisories_triggered
        return json.dumps(payload, indent=2, default=str)

    advisories_triggered = _run_advisory_detection(ns, scope, code)
    payload = {
        "scope": scope,
        "result": repr(ns.get("result", "<no `result` assigned>")),
        "stdout": buf.getvalue(),
    }
    if advisories_triggered:
        payload["advisories_triggered"] = advisories_triggered
    return json.dumps(payload, indent=2, default=str)


@mcp.tool(
    description=(
        "Return source mapping doc (docs/deep/SOURCES.md)."
    )
)
def get_fpf_source_mapping() -> str:
    if not SOURCES_MD.is_file():
        return f"ERROR: {SOURCES_MD} not found"
    return SOURCES_MD.read_text(encoding="utf-8")


@mcp.tool(
    description=(
        "Return spec-to-code gap backlog (docs/deep/FPF_SOURCE_TO_CODE_RELATION_AUDIT.md). "
        "Use status_filter to narrow rows."
    )
)
def get_audit_gaps(status_filter: str = "") -> str:
    if not AUDIT_MD.is_file():
        return f"ERROR: {AUDIT_MD} not found"
    text = AUDIT_MD.read_text(encoding="utf-8")
    if not status_filter.strip():
        return text

    needle = status_filter.strip().lower()
    lines = text.splitlines()
    header_end = next((i for i, ln in enumerate(lines) if re.match(r"^\| --- \|", ln)), None)
    if header_end is None:
        return text  # not a table — return unfiltered rather than guess

    preamble = lines[: header_end + 1]
    rows = [ln for ln in lines[header_end + 1 :] if ln.strip().startswith("|") and needle in ln.lower()]
    if not rows:
        return f"(no rows matching status_filter={status_filter!r})"
    return "\n".join(preamble + rows)


@mcp.tool(
    description=(
        "Return integrator advisories (docs/deep/ADVISORIES.md)."
    )
)
def get_advisories() -> str:
    if not ADVISORIES_MD.is_file():
        return f"ERROR: {ADVISORIES_MD} not found"
    return ADVISORIES_MD.read_text(encoding="utf-8")


@mcp.tool(
    description=(
        "Return the durable log of advisory conditions (ADV-01..ADV-08) triggered by past "
        "run_scenario calls on this host — so a session can check what was already found "
        "instead of missing it or rediscovering it from scratch. limit caps how many recent "
        "entries come back (most recent first). Not a fix, not enforcement — awareness only."
    )
)
def get_advisory_log(limit: int = 20) -> str:
    if not ADVISORY_LOG.is_file():
        return json.dumps({"entries": [], "note": "no advisories triggered yet on this host"}, indent=2)
    lines = ADVISORY_LOG.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(ln) for ln in lines if ln.strip()]
    entries.reverse()
    return json.dumps({"entries": entries[: max(0, limit)], "total_logged": len(entries)}, indent=2, default=str)


@mcp.tool(description="Run the existing self-verification harness (python -m fpf_thinking_map.verify).")
def run_verify() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "fpf_thinking_map.verify"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return f"ERROR: verify exit {proc.returncode}\n{out}"
    return out.strip() or "OK"


if __name__ == "__main__":
    mcp.run(transport="stdio")
