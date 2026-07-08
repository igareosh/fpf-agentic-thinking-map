"""fpf-thinking-map test MCP — broad scenario testing against FPF semantics.

Dev-only tool. Not shipped in the PyPI package (lives outside fpf_thinking_map/,
excluded from the build by pyproject.toml's packages.find include list).

verify.py proves the engine's own logic is internally consistent. It does not
prove the compiled map covers the breadth of what the original FPF spec
describes — examples.py has exactly one domain (deploy decision, 5 scenarios).
This server exposes the engine's construction/traversal surface generically,
plus the two documents that already ground FPF semantics in this repo
(SOURCES.md, FPF_SOURCE_TO_CODE_RELATION_AUDIT.md), so an LLM session can
construct new scenarios ad hoc and drive them against known, cited gaps
instead of the ~20 hand-picked fixtures already in verify.py.

Run: python -m dev_mcp.server  (from the repo root, with fpf_thinking_map
installed — `pip install -e .` first)
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fpf-thinking-map-test")

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_MD = REPO_ROOT / "fpf_thinking_map" / "SOURCES.md"
AUDIT_MD = REPO_ROOT / "fpf_thinking_map" / "FPF_SOURCE_TO_CODE_RELATION_AUDIT.md"


@mcp.tool(
    description=(
        "Run arbitrary Python constructing/driving a fpf_thinking_map scenario. "
        "All fpf_thinking_map primitives, state, guards, logic, and traversal classes "
        "are pre-imported. Assign to `result` for it to be returned. This is the same "
        "thing examples.py and verify.py's check_* functions do in code — this just "
        "gives it a tool-call interface instead of an edit-and-reinstall cycle."
    )
)
def run_scenario(code: str) -> str:
    ns: dict = {}
    exec("from fpf_thinking_map import *", ns)  # noqa: S102 — local dev tool, not a security boundary
    exec("from fpf_thinking_map.traversal import ThinkingMapTraversal, Outcome, OutcomeKind", ns)
    exec("from fpf_thinking_map.guards import GuardEngine, GuardVerdict, GuardScope", ns)
    exec("from fpf_thinking_map.logic import LogicLayer, DecisionRule, RuleKind, EvidenceFresh", ns)

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)  # noqa: S102 — see docstring
    except Exception as exc:  # noqa: BLE001 — reporting the failure IS the point of this tool
        return json.dumps(
            {"error": f"{type(exc).__name__}: {exc}", "stdout": buf.getvalue()},
            indent=2, default=str,
        )

    return json.dumps(
        {"result": repr(ns.get("result", "<no `result` assigned>")), "stdout": buf.getvalue()},
        indent=2, default=str,
    )


@mcp.tool(
    description=(
        "Primitive -> FPF spec section mapping (SOURCES.md). Read before constructing "
        "a scenario meant to probe a specific FPF concept (e.g. A.2.7 role incompatibility)."
    )
)
def get_fpf_source_mapping() -> str:
    if not SOURCES_MD.is_file():
        return f"ERROR: {SOURCES_MD} not found"
    return SOURCES_MD.read_text(encoding="utf-8")


@mcp.tool(
    description=(
        "50-item FPF-spec-to-code gap backlog (R01-R50), each with spec line citations "
        "and a status: missing / partial / wrong-shape. Optional status_filter narrows "
        "to matching rows (case-insensitive substring, e.g. 'missing'). Use this as a "
        "menu of known, cited gaps to target with run_scenario."
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
