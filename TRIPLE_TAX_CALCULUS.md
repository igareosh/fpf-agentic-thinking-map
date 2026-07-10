# Triple Tax Calculus

## Cost Function

`Cost(pass_i) = tokens_in + tokens_out + attention_entropy_penalty(vocabulary_novelty)`

Measured here:

- `tokens_in`: exact `tiktoken` counts on the chosen encoding
- `tokens_out`: measured for the compiled live probe; raw live probing was not attempted because the full upstream spec is far beyond a practical live context window
- `attention_entropy_penalty`: approximation, not direct measurement; modeled with subword fragmentation and Zipf-frequency rarity

Encoding note:

- `tiktoken` encoding: `o200k_base`
- `gpt-5.4-mini` is not mapped by `tiktoken`, so this run pins the closest OpenAI-compatible tokenizer family explicitly

## Method

- Upstream spec snapshot: `https://raw.githubusercontent.com/ailev/FPF/d77339d7056433de3ee55ad863860ee4b3006f6f/FPF-Spec.md`
- Upstream commit: `d77339d7056433de3ee55ad863860ee4b3006f6f`
- Spec file: `/home/igareosh/.cache/fpf-agentic-thinking-map/d77339d7056433de3ee55ad863860ee4b3006f6f/FPF-Spec.md`
- Reference vocabulary: Pride and Prejudice (Project Gutenberg)
- Decision points are built only from shipped examples in `fpf_thinking_map/examples.py`
- Full traversal is the shipped deploy walk, measured from the same public API surface

## Vocabulary Novelty

| Corpus | Words | Mean pieces/word | Median pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf | Median Zipf |
|---|---:|---:|---:|---:|---:|---:|---:|
| FPF-Spec.md | 1203688 | 1.341 | 1.000 | 25.6% | 8.9% | 4.913 | 4.870 |
| General English prose | 123682 | 1.259 | 1.000 | 21.8% | 3.2% | 5.800 | 6.100 |

Approximation note:

- The penalty term is a proxy, not an attention-meter
- For the spec corpus, the fragmentation gap over common English is `0.082` pieces/word
- The normalized multiplier is `1.065x` relative to the reference vocabulary

## Raw vs Compiled

| Decision point | Transition | Body tokens | Body chars | Mean pieces/word | Split rate | Note |
|---|---|---:|---:|---:|---:|---|
| missing_pre_approval | ready_to_deploy | 487 | 1783 | 1.233 | 20.5% | single evidence path, gate should still complain about missing approval |
| missing_after_approval | ready_to_deploy | 496 | 1809 | 1.188 | 16.7% | same move, but evidence is complete |
| role_conflict | ready_to_deploy | 516 | 1872 | 1.196 | 17.6% | same transition, but incompatible roles are active |
| full_traversal_step_1 | assess_to_ready | 412 | 1519 | 1.208 | 18.4% | first move in the shipped full traversal |
| full_traversal_step_2 | ready_to_deploy | 496 | 1809 | 1.188 | 16.7% | after the first transition in the shipped full traversal |

### Aggregate

- Mean compiled body tokens across the 5 decision points: `481.4`
- Total compiled body tokens across the 5 decision points: `2407`
- Raw spec body tokens: `2247567`
- Absolute token gap per decision point (raw spec minus mean compiled slice): `2247085.6`
- Raw/compiled mean ratio: `4668.8x`

## Full Traversal

| Step | State | Transition | Outcome | Body tokens | Cumulative |
|---|---|---|---|---:|---:|
| 1 | assessing | assess_to_ready | continue | 409 | 409 |
| 2 | ready_for_decision | ready_to_deploy | continue | 493 | 902 |
| 3 | deploying | - | continue | 353 | 1255 |

- Observed growth shape: `mixed`
- Traversal total body tokens: `1255`
- Step 2 vs step 1: +84 tokens (+20.5%)
- Step 3 vs step 2: -140 tokens (-28.4%)

## Verdict

- 3-pass structure: `self-reported-0-passes`
- Compounding: `mixed`
- Compiled slice advantage over raw spec: `4668.8x`
- Live completion run: `run`
- Raw live completion: `not-attempted-context-overrun`
- Raw live probe note: FPF-Spec.md is 2,247,567 tokens on o200k_base, which is beyond practical live-context probing.
- Live model: `gpt-5.4-mini`
- Live reasoning effort: `high`
- Live latency: `6.73s`
- Live input tokens: `543`
- Live output tokens: `570`
- Live total tokens: `1113`
- Live self-reported pass count: `0`
- Live self-reported pass labels: `[]`

## Disclosure

Full disclosure of who executed what, as of 2026-07-10 — two different AI systems touched this document, and the record should say so plainly rather than let it read as one continuous authorial voice.

- **OpenAI (Codex)** — authored `scripts/triple_tax_calculus.py`, executed it, and wrote the first version of this report (commits `732955f`, `bdca6d9`). The live-probe model queried inside the script was `gpt-5.4-mini`, OpenAI, reasoning effort `high`.
- **Anthropic (Claude, Claude Code session)** — tasked by igareosh with independent validation, not just review. Reproduced every deterministic number in a clean venv with zero live API calls (raw spec token count, mean compiled slice tokens, vocabulary novelty stats, traversal deltas — all matched bit-for-bit). Found and fixed two real problems in Codex's output: a stale `SIGNED: Research (Colombo)` line hardcoded in the script's own markdown generator (would have regenerated the wrong attribution on rerun — Colombo did not do this work), and an overclaim of its own making in `ARCHITECTURE.md`'s caveat text, corrected after re-reading the actual code path (the raw-FPF "3 passes" claim was never live-tested at all — 2,247,567 tokens is past any practical context window — only the compiled side was live-probed, and that probe found 0 self-reported passes, which is consistent with the 1-pass framing, not evidence against the raw side).
- **igareosh (prichindel.com)** — commissioned both the original measurement task and the independent validation pass, reviewed and authorized this disclosure.

The numbers in this document are independently reproducible — see Reproduction below — and have been independently reproduced once, by a different AI system than the one that generated them, with no discrepancy in any deterministic figure. The live-probe figures (input/output tokens, latency, self-reported pass count) were not independently re-run, since that would require live API spend on top of what Codex already spent, and are reported as Codex measured them.

## Reproduction

```bash
pip install -r scripts/requirements-triple-tax.txt
python scripts/triple_tax_calculus.py --write-md TRIPLE_TAX_CALCULUS.md
```
