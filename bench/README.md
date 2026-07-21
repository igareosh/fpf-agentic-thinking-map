# Behavioral ablation harness

Closes the "measurement project, not a code change" item queued on 2026-07-06:
does wiring `fpf_thinking_map` into a real agent's tool surface actually change
its behavior, measured against the same model with no map at all?

Methodology is borrowed from the `Gh-Novel/ThinkMCP-Agentic-Tools` ablation
referenced in that queue note: **same model, same fixed task, one arm has a
tool wired to the map and visible, the other has only a generic action tool
and the same policy stated as prose**. No LLM judge, no output-quality
scoring — per this repo's own scope discipline (see `docs/deep/ADVISORIES.md`
and the scope-framing rule in the parent project), this measures **behavior
only**: tool-call count, policy violations, and back-to-back identical calls
(a thrash proxy), never whether the output was "smarter."

## What's actually being compared

Two fixed tasks, run twice each:

- **`with_map`** — the model gets a tool wired to the real, installed
  `fpf_thinking_map` engine (`ActiveState.attempt_transition` /
  `ThinkingMapTraversal.attempt_bridge`, the exact same calls a production
  MCP wrapper makes). No mocking.
- **`without_map`** — the model gets a single generic action tool with no
  gating. The same policy ("this needs human authorization," "this bridge
  is uncertified for high-risk reports") is stated only as prose in the task
  description — modeling how the constraint exists in any deployment that
  hasn't wired the map in.

Task A (`A_destructive`) reuses `build_destructive_action_map()` from
`fpf_thinking_map.examples` verbatim — the library's own Ignition Lock
scenario, not an invented one. Task B (`B_bridge`) is a small new map built
for this harness: an unlicensed, high-risk bridge crossing with a slower,
correct manual-reconciliation path available as the safe alternative.

## Running it

```bash
pip install -r bench/requirements.txt
export OPENAI_API_KEY=...
python bench/ablation_harness.py 5   # 5 reps per (task, arm) — default 3
```

Writes `bench/raw_results.json`. Model is set via `BENCH_MODEL` — required,
no default hardcoded on purpose. Deliberately not named in this doc or in
`RESULTS.md` either;
the findings are about a capability class shared across current frontier
models, not a claim about one vendor.

## Results

See `RESULTS.md` for the honest writeup — including the parts that don't
flatter the library.

## Limitations, stated up front

- One model family, one provider, one run size (5 reps). This is a first
  data point, not a verdict.
- Both tasks are small and synthetic. Neither adversarially probes a model
  trying to route around the gate on purpose — this only measures a
  cooperative model's default behavior.
- Doesn't touch session persistence (`ADV-08`) or multi-agent contention —
  those are separate, harder measurement problems this harness doesn't
  attempt.
