# dev_mcp — canonical test MCP for fpf-thinking-map

**Dev-only. Not shipped in the PyPI package.** `pyproject.toml` only builds
`fpf_thinking_map*`, so this directory never ends up in the wheel — no
config needed to keep it out.

## What this is for

`verify.py` proves the engine's own logic is internally consistent — it does
not prove the compiled map covers the breadth of what the original FPF spec
describes. `examples.py` has exactly one domain (deploy decision, 5
scenarios). This server exposes the engine's construction/traversal surface
generically, plus the two documents that already ground FPF semantics in
this repo, so you can construct new scenarios ad hoc and drive them against
*known, cited* gaps instead of only the ~22 hand-picked fixtures already in
`verify.py`.

## Tools

- **`run_scenario(code)`** — run arbitrary Python with all `fpf_thinking_map`
  primitives/state/guards/logic/traversal pre-imported. Assign to `result`
  to get it back. Same thing `examples.py` does in code, as a tool call.
- **`get_fpf_source_mapping()`** — `SOURCES.md`: which FPF spec section each
  primitive is supposed to enforce.
- **`get_audit_gaps(status_filter)`** — the 50-item `FPF_SOURCE_TO_CODE_RELATION_AUDIT.md`
  backlog (R01–R50), optionally filtered to `missing` / `partial` / `wrong-shape`
  rows. A menu of known gaps to target.
- **`run_verify()`** — runs `python -m fpf_thinking_map.verify` (the existing
  22-check harness) via subprocess. Logic tests stay reachable from here too.

## Install & register

```bash
pip install -e .              # from repo root — installs fpf_thinking_map
pip install -r dev_mcp/requirements.txt
```

Claude Code (project-scoped, from repo root):

```bash
claude mcp add fpf-test -- python dev_mcp/server.py
```

Or by hand in `.mcp.json`:

```json
{
  "mcpServers": {
    "fpf-test": {
      "command": "python",
      "args": ["dev_mcp/server.py"]
    }
  }
}
```

## Example session

```
get_audit_gaps("missing")
# → pick R16: "no ⊗ role-bundle satisfaction check exists"

run_scenario("""
sm = SemanticMap()
sm.register_context(ContextPrimitive("ctx", "Test"))
sm.register_role(RolePrimitive("r1", "Role A", "ctx"))
sm.register_role(RolePrimitive("r2", "Role B", "ctx"))
# ... construct a bundle scenario, see what the engine actually does
# when neither role alone should satisfy a bundle requirement
result = "describe what you observed"
""")
```

If the outcome doesn't match what `SOURCES.md`/the audit say it should,
that's a real finding — write it up the same way `#26`/`#28` started:
a genuine gap, not a paper-parity feature.
