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

Expect: `STATUS: ALL PASS` (25/25).

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
- `get_advisory_log(limit)` — read back past advisory triggers (see below)

Deep docs used by these tools are under `docs/deep/`.

## Advisory-trigger awareness (not a fix, not enforcement)

Every `run_scenario` call is checked, after execution, against all 8
conditions documented in `docs/deep/ADVISORIES.md`. If any `ActiveState`
object built by the scenario happens to sit in the exact structural
situation an advisory describes, the response carries an
`advisories_triggered` list — and the hit is appended to a durable log
(`dev_mcp/.state/advisory_log.jsonl`, gitignored, local to whatever host
runs the server) so a later session can call `get_advisory_log()` and see
what was already found instead of missing it or rediscovering it from
scratch.

This changes nothing about engine behavior — no move is blocked, no
outcome is altered. It is a testing-awareness layer only. Detector logic
lives in `dev_mcp/advisory_detectors.py`, one function per advisory, each
citing the exact `ADVISORIES.md` "What" clause it mirrors. Four of the
detectors (`ADV-02`, `ADV-03`, `ADV-06`, `ADV-08`) are tiered
`"structural-fact"` — they fire whenever the documented precondition
holds (e.g. risk_level is elevated), which is the engine's normal,
by-design behavior, not a discovered anomaly. The rest (`ADV-01`,
`ADV-05`, `ADV-07`) are tiered `"anomaly"` — they only fire when the
scenario's own objects show the specific mismatch. `ADV-04` is
`"heuristic-prompt"` — best-effort, since inferring "these two actions
are meant to be opposites" is exactly the semantic judgment the advisory
says the engine doesn't make.

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
