# dev_mcp (simple operator guide)

`dev_mcp` is a **dev-only** MCP server for testing `fpf_thinking_map`.
It is **not** shipped in the PyPI package.

If you only need one message: this server lets you run scenarios and inspect behavior quickly.

## Quick start (3 commands)

Run from repo root:

```bash
pip install -e .
pip install -r dev_mcp/requirements.txt
python -m dev_mcp.test_server
```

Expect: `STATUS: ALL PASS` (13/13).

## Start MCP server

```bash
python -m dev_mcp.server
```

Or register in your MCP client:

```json
{
  "mcpServers": {
    "fpf-test": {
      "command": "python",
      "args": ["-m", "dev_mcp.server"]
    }
  }
}
```

## Scope rule (important)

`run_scenario(code, scope)` requires one of:

- `scope="core"` — testing the shipped library itself
- `scope="user-extension"` — testing your own map built on top

This is for tracking ownership of findings.

## Tools (short)

- `run_scenario(code, scope)` — run scenario code (`result` is returned)
- `run_verify()` — run `python -m fpf_thinking_map.verify`
- `get_fpf_source_mapping()` — open source mapping doc
- `get_audit_gaps(status_filter)` — open known gap backlog
- `get_advisories()` — open integrator advisories

Deep docs used by these tools are under `docs/deep/`.

## Minimal session example

```python
run_verify()
get_audit_gaps("missing")
run_scenario(
    code="result = 'ok'",
    scope="core",
)
```

If `fpf_thinking_map` is not installed, `run_scenario` returns a clear install hint.
