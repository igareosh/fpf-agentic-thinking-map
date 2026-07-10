# Triple Tax Calculus

This document compares two different things:

- **Raw FPF**: Aliev's `ailev/FPF` framework, tested as raw spec text.
- **fpf-thinking-map**: this repo's compiled map, tested through `state.slice()` and the shipped scenarios.

The purpose is not to say raw FPF is bad. The purpose is to measure what changes when an LLM works from raw FPF versus from fpf-thinking-map.

## Bottom Line

- Raw FPF monolith does not fit. The full spec is **2,247,567** tokens and the live monolith attempt failed with context-length overflow.
- fpf-thinking-map's compiled `state.slice()` averages **481.4** tokens per decision.
- The feasible raw alternative, using the exact cited FPF section-pack instead of the whole monolith, still averages **138977.2** tokens per decision.
- That makes fpf-thinking-map **4668.8x** smaller than the full raw spec and **288.7x** smaller than the raw exact-section prompt.
- In live billed input tokens, fpf-thinking-map averaged **537.4** per decision; the raw exact-section prompt averaged **139194.6**. That is a **259.0x** live cost gap.
- Against this repo's own expected outcomes, fpf-thinking-map matched **80.0%** of shipped cases; the raw exact-section prompt matched **40.0%**.
- The prose `Parse -> Aggregate -> Generate` story is not measured by this harness: it makes exactly `1` LLM call per row, by construction. No self-reported pass count is collected or trusted.
- The shipped multi-step traversal compounds **linearly**, not superlinearly. The shipped traversal here is **3** steps total, with **2** decision-bearing `slice()` steps.

## Cost Function

`Cost(pass_i) = tokens_in + tokens_out + attention_entropy_penalty(vocabulary_novelty)`

Measured directly here:

- `tokens_in`: exact `tiktoken` counts, plus live API billed input tokens when live runs are enabled
- `tokens_out`: live API billed output tokens only
- `attention_entropy_penalty`: approximation only, using subword fragmentation and Zipf rarity

- Encoding: `o200k_base`

## Method

- Raw source pinned to `ailev/FPF` commit `d77339d7056433de3ee55ad863860ee4b3006f6f`
- Raw file path: `/home/igareosh/.cache/fpf-agentic-thinking-map/d77339d7056433de3ee55ad863860ee4b3006f6f/FPF-Spec.md`
- Comparable decision points: 5, all built from `fpf_thinking_map/examples.py`
- Raw conditions tested:
  1. full `FPF-Spec.md` monolith
  2. exact raw section-pack extracted from the FPF sections fpf-thinking-map cites for a given slice
  3. compiled `state.slice()` JSON from fpf-thinking-map
- Live runs were done against one current high-capacity API configuration. The model name is omitted here because the comparison target is raw-vs-compiled, not model-vs-model.

## Vocabulary Novelty

| Corpus | Words | Mean pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf |
|---|---:|---:|---:|---:|---:|
| Raw FPF spec | 1203688 | 1.341 | 25.6% | 8.9% | 4.913 |
| General English prose | 123682 | 1.259 | 21.8% | 3.2% | 5.800 |

- Fragmentation gap over common English: `0.082` pieces/word
- Fragmentation multiplier: `1.065x`

## Exact Token Counts

| Decision point | Expected outcome | fpf-thinking-map tokens | Raw FPF section-pack tokens | Raw/compiled | Full raw spec tokens |
|---|---|---:|---:|---:|---:|
| missing_pre_approval | collect_evidence | 487 | 140664 | 288.8x | 2247567 |
| missing_after_approval | continue | 496 | 140664 | 283.6x | 2247567 |
| role_conflict | denied | 516 | 140664 | 272.6x | 2247567 |
| full_traversal_step_1 | continue | 412 | 132230 | 320.9x | 2247567 |
| full_traversal_step_2 | continue | 496 | 140664 | 283.6x | 2247567 |

- Mean fpf-thinking-map slice body: `481.4` tokens
- Mean raw FPF section-pack body: `138977.2` tokens
- Full raw spec minus mean fpf-thinking-map slice: `2247085.6` tokens
- Mean raw section-pack minus mean fpf-thinking-map slice: `138495.8` tokens

## Why fpf-thinking-map Exists, Now Measured

- Raw FPF as a monolith is too large to feed directly.
- Even after reducing raw FPF to only the exact cited sections relevant to one decision, the prompt is still about `139k` tokens on average.
- fpf-thinking-map collapses that same decision surface to about `481` tokens on average.
- So fpf-thinking-map is not merely a convenience layer. It is a context-fit layer and a cost-control layer.

## Live Results

| Decision point | Condition | Expected | Predicted | Match | Input tokens | Output tokens | Latency |
|---|---|---|---|---:|---:|---:|---:|
| missing_pre_approval | compiled_slice | collect_evidence | collect_evidence | yes | 543 | 84 | 2.51s |
| missing_pre_approval | raw_section_pack | collect_evidence | collect_evidence | yes | 140883 | 170 | 4.12s |
| missing_after_approval | compiled_slice | continue | continue | yes | 552 | 113 | 2.78s |
| missing_after_approval | raw_section_pack | continue | collect_evidence | no | 140889 | 226 | 3.90s |
| role_conflict | compiled_slice | denied | continue | no | 572 | 98 | 2.26s |
| role_conflict | raw_section_pack | denied | escalate | no | 140867 | 224 | 4.51s |
| full_traversal_step_1 | compiled_slice | continue | continue | yes | 468 | 79 | 1.54s |
| full_traversal_step_1 | raw_section_pack | continue | continue | yes | 132449 | 233 | 6.93s |
| full_traversal_step_2 | compiled_slice | continue | continue | yes | 552 | 134 | 3.97s |
| full_traversal_step_2 | raw_section_pack | continue | escalate | no | 140885 | 230 | 7.36s |

| Condition | Accuracy | Mean input tokens | Mean output tokens | Mean latency |
|---|---:|---:|---:|---:|
| compiled_slice | 80.0% | 537.4 | 101.6 | 2.61s |
| raw_section_pack | 40.0% | 139194.6 | 216.6 | 5.36s |

### Read Of These Live Results

- fpf-thinking-map wins hard on prompt size and speed.
- Raw exact-section prompting preserves more of raw FPF's stricter ontology, but it also stops agreeing with fpf-thinking-map on several shipped cases.
- That disagreement is useful. It tells us where fpf-thinking-map is operationalizing raw FPF rather than reproducing it literally.

### Pass Count

- Not measured by introspection. This harness makes exactly `1` LLM call per (point, condition) row, by construction (see `measure_live_json` — one `client.responses.create` per row).
- No claim is made about how many reasoning passes happen inside that one call. Any "N-pass" claim requires N separate, counted calls with distinct prompts — not a self-reported field.

## Full Raw Monolith Attempt

- Raw full-spec body tokens: `2247567`
- Raw full-spec prompt tokens (with scenario facts): `2247734`
- Live status: `error`
- Live error: `BadRequestError("Error code: 400 - {'error': {'message': 'Your input exceeds the context window of this model. Please adjust your input and try again.', 'type': 'invalid_request_error', 'param': 'input', 'code': 'context_length_exceeded'}}")`

Interpretation:

- This is the cleanest proof in the file that raw FPF is not directly usable as a one-shot prompt source for current LLM practice.
- fpf-thinking-map exists partly because the framework does not fit.

## MCP / Harness Checks

- `python -m fpf_thinking_map.verify`: `PASS`
- `python -m dev_mcp.test_server`: `PASS`
- `dev_mcp.run_scenario` probe: `{'outcome_kind': 'collect_evidence', 'possible_transitions': ['ready_to_deploy', 'ready_to_escalate'], 'blockers': ["missing evidence: ['owner_approval']", "gate 'deploy_gate' abstains — insufficient evidence: ['owner_approval']"], 'gate': {'id': 'deploy_gate', 'label': 'Deployment Gate', 'decision': 'insufficient', 'missing': ['owner_approval']}}`

Interpretation:

- fpf-thinking-map is not just a markdown claim. It is executable, testable, and inspectable through its own verify harness and MCP test surface.

## Compounding

- Shipped full traversal records `3` total steps.
- Decision-bearing `slice()` steps inside that traversal: `2`.
- Cumulative compiled decision-prompt tokens: `914` local, `1020` billed
- Cumulative raw section-pack decision-prompt tokens: `273228` local, `273334` billed
- Decision-step ratio: `298.9x` local, `268.0x` billed
- Growth shape on the shipped traversal: `linear`.
- The line in `WHY_THIS_EXISTS.md` about `36 passes where 6 would suffice` is not directly testable from the shipped example because the shipped example here is 3 steps, not 6. See [Verification](fpf_thinking_map/WHY_THIS_EXISTS.md#verification) in that file for the full audit.

## What The Test Says

### For fpf-thinking-map

- The core existence claim is confirmed: fpf-thinking-map is `4668.8x` smaller than the full raw spec and `288.7x` smaller than the feasible raw exact-section alternative.
- On live runs, compiled input cost averaged `537.4` billed tokens per decision; raw section-pack averaged `139194.6`.
- fpf-thinking-map matched its own shipped expected outcomes on `80.0%` of cases.
- fpf-thinking-map is executable and measurable: `verify` passed and the package-local `dev_mcp` test surface passed.

### For Raw FPF

- Raw FPF monolith still does not fit: the live monolith attempt hard-failed on context length.
- Even when reduced to exact cited sections instead of the full monolith, raw FPF remains very expensive.
- Raw FPF section-pack prompting was stricter than fpf-thinking-map on several cases and only matched `2/5` shipped outcomes. It kept demanding explicit gate / authority structure where fpf-thinking-map is willing to continue.

### fpf-thinking-map Tradeoff

- Plus: fpf-thinking-map makes raw FPF usable inside real context budgets.
- Minus: some raw FPF strictness is flattened away. `role_conflict` is the concrete miss measured here.

### Practical Read

- If a user asks why fpf-thinking-map exists instead of just feeding raw FPF to an LLM, the answer is now measurable: raw FPF does not fit monolithically, and its reduced exact-section form is still around `139k` tokens per decision.
- In live billed input terms, fpf-thinking-map saves about **138657.2 input tokens per decision** versus the feasible raw exact-section prompt.
- The test supports the claim that compilation buys context fit, cost reduction, and speed.
- The test does not support a clean literal `3 passes` decomposition.
- The test supports linear accumulation of raw cost over steps, but this repo's shipped traversal does not justify a stronger superlinear claim.

## Reproduction

```bash
pip install -r scripts/requirements-triple-tax.txt
OPENAI_API_KEY=... python scripts/triple_tax_calculus.py \
  --write-md TRIPLE_TAX_CALCULUS.md \
  --json-out triple_tax_calculus.json
```

---

SIGNED: OpenAI Codex + Claude Code | equal-footing FPF audit | 2026-07-10 | one BFF footer
