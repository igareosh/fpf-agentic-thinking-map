"""fpf-thinking-map test MCP — broad scenario testing against FPF semantics.

Dev-only tool. Not shipped in the PyPI package (lives outside fpf_thinking_map/,
excluded from the build by pyproject.toml's packages.find include list).

verify.py proves the engine's own logic is internally consistent. It does not
prove the compiled map covers the breadth of what the original FPF spec
describes — examples.py has exactly one domain (deploy decision, 5 scenarios).
This server exposes the engine's construction/traversal surface generically,
plus the documents that already ground FPF semantics in this repo
(SOURCES.md, FPF_SOURCE_TO_CODE_RELATION_AUDIT.md, ADVISORIES.md), so an LLM
session can construct new scenarios ad hoc and drive them against known,
cited gaps instead of the ~20 hand-picked fixtures already in verify.py.
Findings that turn out to be "the library is minimal here on purpose, but
an integrator needs to know" go into ADVISORIES.md, not the audit backlog —
see get_advisories().

Two modes, one tool, distinguished by who's responsible for a finding:
  - core           — testing fpf_thinking_map's own shipped primitives/engine.
                      Applied inspectfully (a human/LLM reviews each result
                      live). This is the publisher's mode: we seal the
                      default (the shipped package) on release, backed by
                      this kind of testing plus verify.py. Findings here are
                      our responsibility — this repo's tracking, not anyone
                      else's.
  - user-extension  — testing a domain map someone built on top of the
                      shipped primitives, above the general mapping this
                      library ships. Still applied inspectfully via this
                      tool, but the seal (if any) is the user's own to grant
                      — their extension, their context, their repo. Mode 2
                      in the strict sense (the shipped package running
                      "blindly" in someone's production agent, no inspection
                      tooling wrapped around it) isn't part of this server at
                      all — it's just `pip install fpf-thinking-map` used
                      normally, which is the point: dev_mcp only exists for
                      the inspected side of that line.

run_scenario requires scope to be set to one of the above on every call —
mandatory self-tagging, not a permission gate, so a finding can't get
separated from whose responsibility it is.

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
ADVISORIES_MD = REPO_ROOT / "fpf_thinking_map" / "ADVISORIES.md"


_VALID_SCOPES = {"core", "user-extension"}


@mcp.tool(
    description=(
        "Run arbitrary Python constructing/driving a fpf_thinking_map scenario. "
        "All fpf_thinking_map primitives, state, guards, logic, and traversal classes "
        "are pre-imported. Assign to `result` for it to be returned. This is the same "
        "thing examples.py and verify.py's check_* functions do in code — this just "
        "gives it a tool-call interface instead of an edit-and-reinstall cycle.\n\n"
        "scope is mandatory self-tagging, not a permission gate — it declares whose "
        "responsibility a finding is, at the source, so it can't get lost later: "
        "'core' = testing fpf_thinking_map's own shipped primitives/engine (publisher "
        "scope — findings belong in this repo's own tracking, e.g. "
        "FPF_SOURCE_TO_CODE_RELATION_AUDIT.md). 'user-extension' = testing a domain map "
        "someone built on top of the shipped primitives, above the general mapping this "
        "library ships (consumer scope — findings belong in THEIR project, not this one)."
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


@mcp.tool(
    description=(
        "Publisher advisories for integrators (ADVISORIES.md, ships in the PyPI package). "
        "Not defects — places where the library deliberately stays minimal and leaves a real "
        "decision to whoever builds a domain map on top of it, with what the default behavior "
        "is, why, and exactly how to get stricter behavior if your domain needs it. Read this "
        "before assuming default behavior matches what your domain requires."
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
