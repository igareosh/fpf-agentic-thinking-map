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

## The story behind the numbers — why 3 passes, why the increase

Numbers without a mechanism are just numbers. This section is the mechanism, built only from data this repo already publishes — no new measurement, no new guesswork beyond what `SOURCES.md`'s own citation table already commits to on the record.

### Why "3 passes" was ever the hypothesis

`WHY_THIS_EXISTS.md` names Parse, Aggregate, Generate because that's the natural shape of what a model has to do with unfamiliar vocabulary: resolve what the words mean, map that meaning onto the actual question, then answer through whatever framing it just built. It's a reasonable three-beat story. It was never derived from a token count — nobody had one until this document.

### Approximating the raw side from data we already have

The raw spec was never live-tested — 2,247,567 tokens is past any context window worth paying for. But this package already publishes, in `SOURCES.md`, an exact citation for every primitive it compiled: which FPF spec section each one came from. That table is "roughly same logic" on the raw side and the compiled side — the same primitive, cited both places — so it can stand in for a rough proxy the live probe couldn't give us: how many *distinct* FPF spec sections does a raw read have to resolve just to answer one decision this package answers in one JSON read?

Every `slice()` this package returns carries `move` (`TransitionPrimitive`), `evidence` (`EvidencePrimitive`), and `roles` (`RolePrimitive`) unconditionally, plus `gate` (`GatePrimitive`) whenever the transition has one bound — confirmed structurally on all 5 decision points via `run_scenario`, not assumed. Every guard in `guards.BUILTIN_GUARDS` runs on every step regardless of transition, per `guards.py`'s own architecture — so their citations are a fixed baseline, not conditional. Taking the union of `SOURCES.md`'s documented citations for the primitive families present plus the guards that always run:

| Family | Sections cited in `SOURCES.md` |
|---|---|
| `TransitionPrimitive` (always) | A.3.3, B.4, A.2.5 |
| `EvidencePrimitive` (always) | A.10, A.2.4, B.3, B.3.4 |
| `RolePrimitive` (always) | A.2, A.2.1, A.2.7, A.13 |
| `GatePrimitive` (when bound — 4 of 5 points) | A.21, A.19.UNM |
| 6 of 9 guards (always evaluated, only 6 have a citation on record) | A.2.8, A.4, A.7, A.2.6 (net new beyond the above) |

Union, for a decision point with a gate bound: **17 distinct FPF spec sections**, spanning 4 separate parts of a 51,000-line document (the role family, the evidence family, the gate family, and the cross-cutting invariants), just to answer one yes/no move this package answers in a single small JSON. That's a floor, not a ceiling — 3 of the 9 guards (`expired_assignment`, `speech_act_validity`, `context_invariants`) don't have a citation in `SOURCES.md` yet, so the real count is at least 17 and plausibly higher. Worth fixing separately; not done here so this section stays confined to numbers already on the record.

Seventeen-plus distinct sections, spread across four regions of the spec, resolved into one answer, is a lot more textured than a clean 3-beat story. That's the honest reframe: "3 passes" was never wrong as an intuition — raw FPF really does force parse-then-map-then-generate — but a model doing that resolution across 17 scattered concepts has no obvious reason to organize the work into exactly 3 discrete, nameable phases, and the live probe's finding (0 self-reported passes on the compiled side, where there's nothing left to resolve) is consistent with passes being a narrative compression of real, elevated, but *continuous* cost — not a literal 3-step state machine a model would ever introspect and report back cleanly. That reconciles the "untested, not confirmed" verdict above with why the hypothesis still feels right: it's probably an undercount of the mechanism, not an overcount, and either way it was never something a live model was likely to narrate on request.

### Why the traversal went up, then down

The full-traversal table shows +20.5% from step 1 to step 2, then -28.4% from step 2 to step 3. Read as "cost first compounds, then somehow un-compounds," that's confusing. Read against the actual object at each step, it isn't a compounding signal at all — it's two different, boring, fully explained things:

- **Step 1 → step 2 (+84 tokens): a real content increase.** Step 1's transition (`assess_to_ready`) has no gate bound — confirmed via `run_scenario`, `has_gate: False`. Step 2's transition (`ready_to_deploy`) does have a gate bound, and one more evidence item is available by then. The state genuinely carries more — a whole extra `GatePrimitive` object plus its evidence — so the slice is genuinely bigger. Not compounding reasoning cost; more bound state, more JSON.
- **Step 2 → step 3 (-140 tokens): not a real decrease — a representation change.** The traversal table lists step 3 with no `transition_id` (`-`), because by step 3 there are no further transitions from the `deploying` state. When that happens, `measure_full_traversal()` calls `state.to_llm_prompt_state()` instead of `state.slice(transition_id)` — a different function returning a structurally different object (confirmed via source read: `to_llm_prompt_state()` carries `active_roles`, `evidence_status`, `stagnation`, `trace`, an empty `possible_transitions: []`; `slice()` carries `move`, `gate`, `response_contract`, none of which `to_llm_prompt_state()` has). Comparing their token counts is comparing two different shapes, not the same object shrinking. The -28.4% is a measurement artifact of switching representations at the terminal step, not evidence that per-step cost falls as a traversal proceeds. `Compounding: mixed` in the Verdict above is the right label for what was actually measured, but "mixed" undersells it — the correct statement is closer to "not measured cleanly enough to compound or not," since one of the two data points isn't a like-for-like comparison at all.

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

## Who won, and why

Not the question we set out to answer, but it's the honest one, so it gets a section.

Between the two AI systems: neither. Codex built something real — the script runs, the method holds up, most of the report was right the first time. Claude found two defects in it on the validation pass, and one of those two was Claude's own — the first draft of this section overclaimed what the live probe had tested, and that only got caught by going back to `build_report()`'s own comment on the second read. The thing that actually won is the same thing the rest of this repository is built around, stated once already in `REFLECTIONS.md`'s wind-tunnel entry: don't trust a table because it's published and came before you, test it yourself, and when your own test produces a table, don't trust that one either until something independent has tried to break it. That rule doesn't stop applying just because the thing being tested is a report about this package instead of a claim inside it.

Between compiled and raw FPF — the actual engineering question — this is a partial win, and the partial part matters more than the win.

**Confirmed, not asserted, as of this measurement:** the core bet stated in `SOURCES.md`'s "Package authorship" section and argued in prose in `WHY_THIS_EXISTS.md` — that a compiled decision slice costs a small fraction of what the raw 51,000-line spec would cost a model per decision — is no longer a claim resting on the diagram in `ARCHITECTURE.md`. It's 4668.8x, measured on the package's own shipped examples, reproduced bit-for-bit by a second AI system with no access to the first one's numbers going in. `FPF_SCOPE_AUDIT_LOG.md`'s verdict line — "compile the framework away, once, rather than let the model carry it" — has a number behind it now that it didn't have when that log was written.

**Not confirmed, and now correctly labeled as such:** the specific *mechanism* — that raw FPF costs exactly three re-reasoning passes, that cost compounds across a multi-step traversal the way `WHY_THIS_EXISTS.md`'s prose describes. Both were genuinely tested for, and both came back inconclusive rather than confirmed: the raw side was too large to live-test at all, and the compiled side's compounding read came from two deltas on a traversal that terminates in three steps by design. The `REJECTED_*.md` docs in this package all follow the same shape — reject or accept a specific mechanism, not the general instinct behind it. Same move here: the general instinct (raw FPF is expensive, compiled is cheap) is confirmed at a scale that isn't close. The specific mechanistic story about *why*, pass by pass, is still exactly what it was before this measurement — a plausible narrative, not a settled fact — and this document says that outright instead of letting a large, real, unrelated number (4668.8x) quietly launder an unrelated small claim (exactly 3 passes) into looking equally confirmed.

That's the actual scope rail this measurement had to respect: get to use the big win, don't get to borrow its credibility for the part that wasn't tested.

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
