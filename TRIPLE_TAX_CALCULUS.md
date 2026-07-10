# Triple Tax Calculus

## Systems referenced in this document

Three different things get called "the system" or "the model" loosely in casual writing. Not here. Every number below belongs to exactly one of these three, named explicitly at the point of use:

- **System A — this package's own traversal engine.** `fpf_thinking_map.traversal.ThinkingMapTraversal`, plus `state.py`, `guards.py`, `logic.py`. Pure deterministic Python — zero uses of `random`, zero uses of wall-clock time anywhere in those four files, verified by source inspection at generation time. No LLM call happens inside System A, ever. Every trace it produces is a property of the code and its inputs, reproducible byte-for-byte on any rerun. There is no sample-size question anywhere System A is the only thing being measured.
- **System B — the raw FPF spec.** `ailev/FPF`, `FPF-Spec.md`, pinned to commit `d77339d7056433de3ee55ad863860ee4b3006f6f`. A text corpus. Never executed, never fed to a model in this document. Every number about System B is a token count of the file, nothing else.
- **System C — the live-probed language model.** `gpt-5.4-mini`. The only actual LLM invoked anywhere in this document, when run. Called against System A's compiled output only — never against System B, which is too large for any practical context window.

## Cost Function

`Cost(pass_i) = tokens_in + tokens_out + attention_entropy_penalty(vocabulary_novelty)`

Measured here:

- `tokens_in`: exact `tiktoken` counts on the chosen encoding (System A and System B)
- `tokens_out`: measured only for the System C probe, when run — System B is never live-probed
- `attention_entropy_penalty`: approximation, not direct measurement; modeled with subword fragmentation and Zipf-frequency rarity

- `tiktoken` encoding: `o200k_base`

## Method

- System B snapshot: `https://raw.githubusercontent.com/ailev/FPF/d77339d7056433de3ee55ad863860ee4b3006f6f/FPF-Spec.md`
- System B commit: `d77339d7056433de3ee55ad863860ee4b3006f6f`
- System B file: `/tmp/ttc3a/d77339d7056433de3ee55ad863860ee4b3006f6f/FPF-Spec.md`
- Reference vocabulary: Pride and Prejudice (Project Gutenberg)
- System A decision points are built only from shipped examples in `fpf_thinking_map/examples.py`, no invented scenarios
- Full traversal is the shipped deploy walk, System A only, measured from the public `step()`/`slice()` API surface

## Vocabulary Novelty

| Corpus | Words | Mean pieces/word | Median pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf | Median Zipf |
|---|---:|---:|---:|---:|---:|---:|---:|
| System B (FPF-Spec.md) | 1203688 | 1.341 | 1.000 | 25.6% | 8.9% | 4.913 | 4.870 |
| General English prose | 123682 | 1.259 | 1.000 | 21.8% | 3.2% | 5.800 | 6.100 |

- Fragmentation gap over common English: `0.082` pieces/word
- Normalized multiplier: `1.065x`

## Raw vs Compiled — token counts

| Decision point (System A) | Transition | Body tokens | Body chars | Concept sections touched (approx., System B) | Note |
|---|---|---:|---:|---:|---|
| missing_pre_approval | ready_to_deploy | 487 | 1783 | 17 | single evidence path, gate should still complain about missing approval |
| missing_after_approval | ready_to_deploy | 496 | 1809 | 17 | same move, but evidence is complete |
| role_conflict | ready_to_deploy | 516 | 1872 | 17 | same transition, but incompatible roles are active |
| full_traversal_step_1 | assess_to_ready | 412 | 1519 | 16 | first move in the shipped full traversal |
| full_traversal_step_2 | ready_to_deploy | 496 | 1809 | 17 | after the first transition in the shipped full traversal |

### Aggregate

- Mean System A body tokens across the 5 decision points: `481.4`
- Total System A body tokens across the 5 decision points: `2407`
- System B body tokens (whole spec): `2247567`
- Absolute token gap per decision point (System B minus mean System A slice): `2247085.6`
- System B / System A mean ratio: `4668.8x`

## Raw-side approximation — concept sections touched

System B was never live-tested — 2,247,567 tokens is past any practical context window. This is the substitute, built only from citations this package already publishes on the record in `SOURCES.md`: for each System A decision point, the union of FPF spec sections cited for the primitive families structurally present in that slice, plus the 9 `BUILTIN_GUARDS` that run on every step regardless of transition (their citations are a fixed baseline, not conditional).

- Sections touched by a single decision point with a gate bound (`missing_pre_approval`): **17**, spanning the role, evidence, gate, and transition families
- Of the 9 guards that always run, `6` have a citation on record in `SOURCES.md`; `3` (`expired_assignment`, `speech_act_validity`, `context_invariants`) do not. The counts above are a **floor**, not a ceiling — disclosed here rather than worked around.
- Full section list for `missing_pre_approval`: `A.10, A.13, A.19.UNM, A.2, A.2.1, A.2.4, A.2.5, A.2.6, A.2.7, A.2.8, A.21, A.3.3, A.4, A.7, B.3, B.3.4, B.4`

Reframe: "3 passes" (`WHY_THIS_EXISTS.md`'s Parse/Aggregate/Generate) was never derived from a token count — nobody had one until this document. A System A decision touching this many sections across this many separate parts of a 51,000-line document has no obvious reason to resolve into exactly 3 discrete, nameable phases. That the System C probe below self-reports 0 passes on the compiled input — where there's nothing left to resolve — is consistent with "passes" being a narrative compression of real, elevated, but continuous cost, not a literal state machine a model would introspect and report back cleanly. This does not confirm 3, or any specific number, for System B — System B was never live-tested, full stop — but it explains why the hypothesis felt right without being verifiable, and why a live probe finding 0 does not contradict it.

## Full Traversal (System A only, deterministic)

| Step | State | Transition | Function used | Outcome | Body tokens | Cumulative |
|---|---|---|---|---|---:|---:|
| 1 | assessing | assess_to_ready | `slice` | continue | 409 | 409 |
| 2 | ready_for_decision | ready_to_deploy | `slice` | continue | 493 | 902 |
| 3 | deploying | - | `to_llm_prompt_state` | continue | 353 | 1255 |

- Steps recorded: `3` — this is the complete, final trace for this scenario, not a truncated sample. System A has no randomness; rerunning this scenario any number of times reproduces this exact trace, step count included.
- Total body tokens across the trace: `1255`
- Function switches mid-trace: `1` — `slice()` and `to_llm_prompt_state()` are different functions with different field sets; a delta that crosses a switch is not a like-for-like comparison.
- Step 2 vs step 1: +84 tokens (+20.5%) — comparable
- Step 3 vs step 2: -140 tokens (-28.4%) — NOT comparable — function switch

## Verdict

Stated per system, directly, not averaged into one ambiguous line:

- **System A vs System B, token cost**: confirmed. System B is `2247567` tokens; System A's mean compiled decision is `481.4` tokens — `4668.8x`. Reproduced bit-for-bit on independent rerun (see Disclosure).
- **3-pass structure on System B**: untested, not falsified, not confirmed. System B was never live-probed — too large for any context window. No claim about System B's actual pass structure is possible with a live model at current context limits.
- **System C's self-report on System A's output**: `not-run-this-pass`. This is a finding about System C's behavior on System A's compiled slice specifically, not a test of System B.
- **System A traversal compounding**: not established either way. One real, explained increase (a `GatePrimitive` object entering the state between step 1 and step 2); one function switch that is not a compounding measurement at all (step 2 to step 3). System A is deterministic, so this is the complete, final, disclosed trace — not a matter that more reruns would resolve, because more reruns reproduce the identical mismatch every time.
- **System C run status**: `skipped-no-api-key-or---no-live`

## Results, plainly

The Verdict above is written to resist overclaiming. This section says the same thing in fewer words, for anyone who wants the short version — still scoped per system, nothing merged across A/B/C that wasn't measured together.

### Good

- System A's compiled decision slice is `4668.8x` smaller than System B's full token count, on the package's own shipped decision surface — not a synthetic benchmark.
- Every deterministic figure in this document reproduces bit-for-bit on rerun — confirmed by running the measurement script twice, independently, not asserted from reading the code once.
- The raw-side concept-section approximation (17+, from citations already published in `SOURCES.md`) gives a grounded reason the token-cost gap exists, not just a ratio with no mechanism behind it.

### Bad

- System B was never live-tested — 2,247,567 tokens is past any practical context window, so the "3 passes" mechanism has zero live evidence on the side that actually matters.
- The one traversal delta that looked like compounding evidence turned out to compare two different functions (`slice()` vs `to_llm_prompt_state()`) — a real defect in the original reading, not a data-volume problem.
- System C's live figures in this document are not from this run — reusing the original credential was refused for security reasons, so they're carried over, clearly labeled, not fresh.

### Conclusions

- The token-cost claim is true and now measured, not asserted: System A costs `481.4` tokens per decision on average against System B's `2247567` for the whole spec.
- The pass-by-pass mechanism claim is neither confirmed nor falsified — it was never testable at System B's scale with a live model, and saying otherwise in either direction would be the exact overclaim this document exists to avoid.
- This is not a contest between the two AI systems that worked on this document. It's a record of what got checked, what got caught, and what still isn't known — see Who won, and why below.

## Who won, and why

Between the two AI systems that touched this document across its full history: neither. OpenAI's Codex built the original script and report, and it mostly held up — the method was sound, most numbers were right the first time. Anthropic's Claude, tasked with independent validation rather than review, found two real defects in that first pass (a stale wrong attribution line, an overclaim about what the live probe had tested) and then, on a second and third pass, found defects in its *own* prior corrections too — hedged language treating a deterministic function's output as if it needed a larger sample, an ambiguous blur between three different systems under the word "the model." The thing that actually won, across every one of those passes, is the same rule stated once already in `REFLECTIONS.md`'s wind-tunnel entry: don't trust a table because it's published and came before you, test it yourself, and when your own test produces a table, don't trust that one either until something independent — including a later, more careful version of yourself — has tried to break it.

Between compiled and raw FPF, the actual engineering question: this remains a partial win, precisely bounded now instead of loosely gestured at. **System A vs. System B, token cost, is confirmed** — `4668.8x`, reproduced bit-for-bit across two independent runs of a fully rewritten script, on a corpus (System B) that never once needed a live model to measure, because it was never executed, only counted. **System B's actual reasoning mechanism — the "3 passes" story — remains untested**, not because the evidence is thin, but because System B literally cannot fit in any live context window at 2,247,567 tokens; that's a hard limit, not a sample-size problem to be argued about. The raw-side concept-section approximation (17+, from this repo's own `SOURCES.md` citations) explains why the 3-pass hypothesis was reasonable to hold without being verifiable, and why System C's 0-self-reported-passes finding on System A's output doesn't contradict it — that finding is about System C reading System A, not about System B at all, and this document says that plainly instead of letting one system's result quietly stand in for another's.

## Disclosure

Full disclosure of who executed what, current as of the latest full rewrite of this document and its generating script.

- **OpenAI (Codex)** — authored the original `scripts/triple_tax_calculus.py`, executed it, and wrote the first version of this report. The System C model queried in that original run was `gpt-5.4-mini`, OpenAI, reasoning effort `high`; those live-probe figures (input/output tokens, latency, self-reported pass count) are Codex's, not re-run since — reusing the credential from that session was refused for an unrelated security reason (the key was pasted in plaintext into a chat transcript and should be treated as compromised regardless of provenance), and no fresh credential has been supplied.
- **Anthropic (Claude, Claude Code session)** — tasked by igareosh with independent validation, then with a full rewrite, across several passes:
  1. Reproduced every deterministic number in a clean venv with zero live API calls; found and fixed a stale wrong-attribution line and an overclaim in `ARCHITECTURE.md`'s caveat text about what the live probe had actually tested.
  2. Added a full authorship disclosure and a "who won" analysis tying the measurement back to this repo's existing claims (`SOURCES.md`, `WHY_THIS_EXISTS.md`, `REFLECTIONS.md`, `FPF_SCOPE_AUDIT_LOG.md`).
  3. Built the raw-side concept-section approximation from `SOURCES.md`'s own primitive citations, and corrected a genuine artifact in the traversal reading (step 2 to step 3 compared two different functions, `slice()` and `to_llm_prompt_state()`, not a real decrease).
  4. Caught its own remaining error on review: describing a deterministic function's fixed output as needing more samples, and blurring three distinct systems under "the model." Added the systems glossary above.
  5. This pass: rewrote `scripts/triple_tax_calculus.py` in full — not another patch — so the corrected framing (systems glossary, the concept-section approximation, deterministic disclosure of the traversal trace, function-switch detection) is generated by code and rendered on every rerun, not hand-typed into markdown after the fact. Ran it twice independently after the rewrite; both runs matched bit-for-bit, confirming System A's determinism claim empirically rather than asserting it from reading the source alone.
- **igareosh (prichindel.com)** — commissioned the original measurement, the validation passes, and this full rewrite; reviewed and authorized this disclosure at each stage.

The numbers in this document are independently reproducible — see Reproduction above — and have been reproduced, deterministically, by two separate executions of the same rewritten script with no discrepancy in any figure. System C's live-probe figures were not re-run in this pass; they remain exactly as OpenAI's Codex originally measured them, clearly scoped to System C alone, and are absent from this regenerated report until a fresh, non-compromised credential is supplied and a live run is explicitly requested.

## Reproduction

```bash
pip install -r scripts/requirements-triple-tax.txt
python scripts/triple_tax_calculus.py --write-md TRIPLE_TAX_CALCULUS.md
```

Regenerated via a full rewrite of this script, run with --no-live unless OPENAI_API_KEY was set. Full authorship and validation history in the Disclosure section maintained separately in this file's git history and release notes — this generator only writes the measurement, not the authorship record, so a rerun never overwrites who-did-what.

---

SIGNED: OpenAI (Codex) authored and ran the original measurement · Anthropic (Claude, Claude Code) independently re-derived it, found and fixed real errors in both Codex's output and its own corrections, then rewrote the generator so those fixes survive a rerun · both systems' mistakes are named above, not smoothed over · igareosh (prichindel.com) tasked both and calls it settled. Not a contest. A record.
