# Triple Tax Calculus

## Verdict

- Full raw FPF monolith is **2,247,567** tokens. Live attempt on `gpt-5.4`: `error` (`BadRequestError("Error code: 400 - {'error': {'message': 'Your input exceeds the context window of this model. Please adjust your input and try again.', 'type': 'invalid_request_error', 'param': 'input', 'code': 'context_length_exceeded'}}")`)
- Compiled `state.slice()` mean size: **481.4** tokens.
- Raw exact section-pack mean size: **138977.2** tokens.
- Compiled is **4668.8x** smaller than the full raw spec and **288.7x** smaller than the feasible raw section-pack.
- Live billed input mean on `gpt-5.4`: compiled **558.4** vs raw section-pack **139215.6** tokens (**249.3x**).
- Live accuracy against the package's own engine: compiled **80.0%**, raw section-pack **40.0%**.
- The prose `Parse -> Aggregate -> Generate` claim does **not** show up as a stable measured 3-pass decomposition: `unstable-self-report-[0, 1, 3, 1]`.
- Multi-step compounding over the shipped traversal is **linear**, not superlinear. The shipped full traversal records **3** steps, not 6.

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
  2. exact raw section-pack extracted from the FPF sections this package cites for that slice
  3. compiled `state.slice()` JSON
- Live model: `gpt-5.4`
- Live reasoning effort: `low`

## Vocabulary Novelty

| Corpus | Words | Mean pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf |
|---|---:|---:|---:|---:|---:|
| Raw FPF spec | 1203688 | 1.341 | 25.6% | 8.9% | 4.913 |
| General English prose | 123682 | 1.259 | 21.8% | 3.2% | 5.800 |

- Fragmentation gap over common English: `0.082` pieces/word
- Fragmentation multiplier: `1.065x`

## Exact Token Counts

| Decision point | Expected outcome | Compiled slice tokens | Raw section-pack tokens | Raw/compiled | Full raw spec tokens |
|---|---|---:|---:|---:|---:|
| missing_pre_approval | collect_evidence | 487 | 140664 | 288.8x | 2247567 |
| missing_after_approval | continue | 496 | 140664 | 283.6x | 2247567 |
| role_conflict | denied | 516 | 140664 | 272.6x | 2247567 |
| full_traversal_step_1 | continue | 412 | 132230 | 320.9x | 2247567 |
| full_traversal_step_2 | continue | 496 | 140664 | 283.6x | 2247567 |

- Mean compiled slice body: `481.4` tokens
- Mean raw section-pack body: `138977.2` tokens
- Full raw spec minus mean compiled slice: `2247085.6` tokens
- Mean raw section-pack minus mean compiled slice: `138495.8` tokens

## Live Results

| Decision point | Condition | Expected | Predicted | Match | Input tokens | Output tokens | Latency |
|---|---|---|---|---:|---:|---:|---:|
| missing_pre_approval | compiled_slice | collect_evidence | collect_evidence | yes | 564 | 119 | 2.57s |
| missing_pre_approval | raw_section_pack | collect_evidence | collect_evidence | yes | 140904 | 318 | 5.40s |
| missing_after_approval | compiled_slice | continue | continue | yes | 573 | 144 | 2.52s |
| missing_after_approval | raw_section_pack | continue | collect_evidence | no | 140910 | 265 | 4.56s |
| role_conflict | compiled_slice | denied | continue | no | 593 | 186 | 3.35s |
| role_conflict | raw_section_pack | denied | denied | yes | 140888 | 212 | 3.84s |
| full_traversal_step_1 | compiled_slice | continue | continue | yes | 489 | 137 | 2.53s |
| full_traversal_step_1 | raw_section_pack | continue | escalate | no | 132470 | 293 | 5.03s |
| full_traversal_step_2 | compiled_slice | continue | continue | yes | 573 | 147 | 3.32s |
| full_traversal_step_2 | raw_section_pack | continue | escalate | no | 140906 | 268 | 4.46s |

| Condition | Accuracy | Mean input tokens | Mean output tokens | Mean latency |
|---|---:|---:|---:|---:|
| compiled_slice | 80.0% | 558.4 | 146.6 | 2.86s |
| raw_section_pack | 40.0% | 139215.6 | 271.2 | 4.66s |

### 3-Pass Claim Test

- Self-reported pass counts are unstable, mostly `null`.
- `missing_pre_approval` / `compiled_slice` -> `pass_count=0` `pass_labels=[]`
- `missing_after_approval` / `compiled_slice` -> `pass_count=1` `pass_labels=['Deployment Gate']`
- `role_conflict` / `compiled_slice` -> `pass_count=3` `pass_labels=['Deployment Gate', 'owner_approval', 'test_results']`
- `full_traversal_step_2` / `compiled_slice` -> `pass_count=1` `pass_labels=['Deployment Gate']`

## Full Raw Monolith Attempt

- Raw full-spec body tokens: `2247567`
- Raw full-spec prompt tokens (with scenario facts): `2247734`
- Live status: `error`
- Live error: `BadRequestError("Error code: 400 - {'error': {'message': 'Your input exceeds the context window of this model. Please adjust your input and try again.', 'type': 'invalid_request_error', 'param': 'input', 'code': 'context_length_exceeded'}}")`

## MCP / Harness Checks

- `python -m fpf_thinking_map.verify`: `PASS`
- `python -m dev_mcp.test_server`: `PASS`
- `dev_mcp.run_scenario` probe: `{'outcome_kind': 'collect_evidence', 'possible_transitions': ['ready_to_deploy', 'ready_to_escalate'], 'blockers': ["missing evidence: ['owner_approval']", "gate 'deploy_gate' abstains — insufficient evidence: ['owner_approval']"], 'gate': {'id': 'deploy_gate', 'label': 'Deployment Gate', 'decision': 'insufficient', 'missing': ['owner_approval']}}`

## Compounding

- Shipped full traversal records `3` total steps.
- Decision-bearing `slice()` steps inside that traversal: `2`.
- Cumulative compiled decision-prompt tokens: `914` local, `1062` billed
- Cumulative raw section-pack decision-prompt tokens: `273228` local, `273376` billed
- Decision-step ratio: `298.9x` local, `257.4x` billed
- Growth shape on the shipped traversal: `linear`. Each extra decision step resends another prompt; no superlinear explosion showed up in this repo's own traversal.
- `WHY_THIS_EXISTS.md`'s `36 passes where 6 would suffice` line is not directly testable from the shipped example because the shipped example is 3 steps, not 6.

## Results, Plainly

### Good

- The token-tax claim is real: compiled `state.slice()` is `4668.8x` smaller than the full raw spec and `288.7x` smaller than the exact raw section-pack.
- On live runs, compiled input cost averaged `558.4` billed tokens per decision; raw section-pack averaged `139215.6`.
- Compiled matched the package's own engine on `80.0%` of shipped cases.
- The local package checks are green: `verify` passed and the package-local `dev_mcp` test surface passed.

### Bad

- The full raw spec still does not fit: the live monolith attempt hard-failed on context length.
- The compiled slice missed the `role_conflict` case in live evaluation: the slice does not carry the role-incompatibility relation explicitly enough for the model to recover the package's `denied` outcome.
- The raw section-pack was stricter than the package on several cases and only matched 2/5 shipped outcomes. It kept asking for explicit gate/authority structure where the compiled package is willing to continue.

### Plus / Minus

- Plus for compiled: very cheap, usually enough, clearly operational.
- Minus for compiled: some semantics are flattened away; `role_conflict` is the concrete miss in this measurement.
- Plus for raw sections: preserves more of FPF's stricter gate / authority story.
- Minus for raw sections: still expensive, slower, and often does not reproduce the package's chosen operational simplification.

### Conclusions

- If the comparison target is the full raw FPF document, the compiled slice is cheaper by **2247085.6 tokens per decision on average**.
- If the comparison target is the feasible raw exact-section prompt a model can actually ingest, the compiled slice is cheaper by **138657.2 billed input tokens per decision on average**.
- The exact `3 passes` claim is not supported by measurement here. The live model did not stably self-report `Parse`, `Aggregate`, `Generate`.
- The compounding claim is directionally true in the simple sense that raw prompts stay expensive every step, but the shipped traversal shows linear accumulation, not a measured superlinear curve.

## Reproduction

```bash
pip install -r scripts/requirements-triple-tax.txt
OPENAI_API_KEY=... python scripts/triple_tax_calculus.py \
  --live-model gpt-5.4 \
  --live-effort low \
  --write-md TRIPLE_TAX_CALCULUS.md \
  --json-out triple_tax_calculus.json
```

---

SIGNED: OpenAI Codex + Claude Code | equal-footing FPF audit | 2026-07-10 | one BFF footer
