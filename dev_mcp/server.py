"""dev_mcp server for agentic testing of fpf_thinking_map.

Agent-first summary:
- Run scenarios quickly: run_scenario(code, scope)
- Run shipped verification: run_verify()
- Read deep docs when needed: sources, gap audit, advisories

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
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fpf-thinking-map-test")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEEP_DOCS = REPO_ROOT / "docs" / "deep"
SOURCES_MD = DEEP_DOCS / "SOURCES.md"
AUDIT_MD = DEEP_DOCS / "FPF_SOURCE_TO_CODE_RELATION_AUDIT.md"
ADVISORIES_MD = DEEP_DOCS / "ADVISORIES.md"


_VALID_SCOPES = {"core", "user-extension"}


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
        return json.dumps(
            {"scope": scope, "error": f"{type(exc).__name__}: {exc}", "stdout": buf.getvalue()},
            indent=2, default=str,
        )

    return json.dumps(
        {
            "scope": scope,
            "result": repr(ns.get("result", "<no `result` assigned>")),
            "stdout": buf.getvalue(),
        },
        indent=2, default=str,
    )


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
