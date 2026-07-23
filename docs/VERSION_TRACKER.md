# Version tracker — v1.0.0 through v1.9.2

Every released version, three practical/reader-facing benefits each — including
doc-only and metadata-only releases, marked as such. This is a supplement to
[`CHANGELOG.md`](../CHANGELOG.md) (which covers v1.6.0 onward in narrative form)
and [`docs/deep/EXPANDED_PROVENANCE.md`](deep/EXPANDED_PROVENANCE.md) (the
v1.7.0–1.9.1 throughline). Full release bodies:
[GitHub Releases](https://github.com/igareosh/fpf-agentic-thinking-map/releases).

There is no v0.x or v1.1.x — v1.0.0 is the first tagged release, and
versioning jumps v1.0.1 → v1.2.0.

---

## v1.9.2 — 2026-07-23 — PyPI presentation alignment (docs-only)

1. Publishes the current reader-facing README to PyPI instead of leaving the
   package page frozen at the earlier v1.9.1 narrative.
2. Makes every README image and repository link portable between GitHub and
   PyPI, including the current test-backed runtime visual.
3. Changes no runtime semantics — package verification remains 26/26 against
   the same v1.9.1 behavior.

## v1.9.1 — 2026-07-23 — Provenance (fix)

1. Closes a real exploit: `AuthorizationReceipt` expiry was checked against
   `step_count`, which never advances for a caller using only
   `attempt_transition()` — a never-consumed receipt validated forever. Fixed
   with a dedicated `_authorization_clock`.
2. No side effects on unrelated behavior — the new clock is deliberately kept
   separate from `step_count`, so evidence TTL decay timing is untouched.
3. Found and confirmed live via adversarial testing (`run_scenario`), not unit
   tests alone — the exact exploit was re-run post-fix and confirmed rejected.

## v1.9.0 — 2026-07-23 — MoveIntent / inspect_move() ("Tail Number")

1. Fixes a real stagnation-detection blind spot — two materially different
   concrete moves sharing a `transition_id` and evidence snapshot used to read
   as the same stagnant retry.
2. Lets a caller inspect a proposed move before firing, with zero risk of
   mutating state (`inspect_move()`).
3. Fully additive — a caller that never constructs a `MoveIntent` sees zero
   behavioral change.

## v1.8.0 — 2026-07-23 — PendingInput / AWAIT ("Holding Pattern")

1. Separates "done" from "blocked on something external" — `AWAIT` stops a
   live external dependency from being misread as `IDLE`'s "nothing left to
   do."
2. Never hides an available move — a candidate action or bridge always wins
   over `AWAIT`.
3. Core stays out of resolution mechanics entirely — `wake_conditions` are
   host/adapter-owned; the engine never polls or resolves anything itself.

## v1.7.0 — 2026-07-23 — AuthorizationReceipt ("Clearance")

1. Closes a replay/TOCTOU hole — approval is bound to one transition and a
   hash of the exact state, not an ambient boolean.
2. Independently re-verified at fire time — transition identity, state
   fingerprint, expiry, and prior consumption are all re-checked, with a
   specific rejection reason on mismatch.
3. Non-breaking — `authorized=True` still works for callers who haven't
   migrated.

## v1.6.0 — 2026-07-20 — Ignition Lock / Abort to Orbit

1. Blocks destructive/high-stakes moves outright — `requires_human_authorization`
   refuses to fire regardless of how legal the move otherwise looks.
2. Tracks concurrent asks correctly — `pending_authorizations` is a set, not a
   single value, so two simultaneous escalations don't clobber each other (a
   real bug caught and fixed the same session).
3. Denial isn't a dead end — `safe_alternatives` plus a recorded
   `deny_pending_authorization(reason)` give a non-destructive path forward
   instead of a silent refusal.

## v1.5.0 — 2026-07-15 — Stop-point / reference release

1. Package folder cleaned to runnable files only — an integrator can tell
   what's actually shipped versus background research at a glance.
2. README repositioned around runtime behavior instead of theory, so the
   "how do I use this" content comes first.
3. MIT-licensed public release — settles the licensing question for anyone
   evaluating it for real use.

## v1.4.25 — 2026-07-10 — version-number consistency (docs-only)

1. Fixed README/badge footers stuck three patch versions behind the actual
   shipped package (showed v1.4.4/1.4.5, real version was 1.4.24).
2. Consolidated a 21-version changelog gap into one entry instead of leaving
   it silently missing.
3. Confirmed — not assumed — zero runtime code changes across that whole
   range before writing the consolidated entry.

## v1.4.24 — 2026-07-10 — docs-only correction

1. Removed an unbacked "36 reasoning passes" claim that no code in the repo
   actually measures.
2. Added a Verification section cross-linking what the measurement harness
   actually supports versus what it doesn't.
3. Removed self-reported `pass_count`/`pass_labels` fields that asked the
   model to narrate its own internals with no causal link to real behavior.

## v1.4.23 — 2026-07-10 — results summary, real signed footer (docs-only)

1. Rebuilt a stale summary against the current System A/B/C structure instead
   of shipping one with broken references.
2. Declined a proposed co-authorship claim on a commit the other party never
   touched — kept attribution accurate over convenient.
3. Verified reproducibility again (two independent runs, bit-for-bit) before
   publishing.

## v1.4.22 — 2026-07-10 — full rewrite, full retest (docs-only)

1. Moved the measurement's key figures from hand-typed markdown to
   code-generated output — removes an entire class of doc/script drift.
2. Added automatic function-switch detection, catching a category of
   measurement bug instead of relying on a human to notice.
3. Retested twice independently, bit-for-bit match — demonstrates the
   determinism claim empirically rather than just asserting it.

## v1.4.21 — 2026-07-10 — unambiguous systems, no more hedging (docs-only)

1. Names exactly which system (A/B/C) every number in the report belongs to —
   stops a reader misapplying a live-model caveat to a deterministic number.
2. Corrects a real prior mischaracterization ("thin evidence") of a fully
   deterministic result.
3. States the actual defect (comparing two different functions' output)
   directly instead of leaving it hedged.

## v1.4.20 — 2026-07-10 — the story behind the numbers (docs-only)

1. Explains why the live probe not finding "3 passes" doesn't contradict the
   original hypothesis.
2. Grounds a new figure (17 FPF sections per decision) in citations already
   in `SOURCES.md` rather than inventing an unverified number.
3. Identifies a measurement-shape artifact (comparing `slice()` versus
   `to_llm_prompt_state()`) so it isn't repeated downstream.

## v1.4.19 — 2026-07-10 — who won, and why (docs-only)

1. States plainly that independent validation — not either AI — is what
   "won," including catching an overclaim one of them introduced.
2. Confirms the core 4668.8x token-cost figure survived a second, independent,
   bit-for-bit reproduction.
3. Explicitly separates what's confirmed (the ratio) from what isn't
   (pass-by-pass mechanism).

## v1.4.18 — 2026-07-10 — full disclosure: dual-AI authorship (docs-only)

1. Names both AI systems involved and exactly what each did and didn't do.
2. Makes the disclosure visible from the installed PyPI package itself, not
   just the GitHub repo.
3. Sets a precedent this repo holds itself to going forward — corrections get
   attributed, not smoothed over.

## v1.4.17 — 2026-07-10 — independent validation of the triple-tax calculus (docs-only)

1. Reproduced every deterministic number from a clean venv, zero live API
   calls — proves the earlier numbers weren't an environment artifact.
2. Caught and fixed a real regression: the report generator still hardcoded a
   wrong attribution line that would have reintroduced it on the next run.
3. Caught and corrected its own overclaim from the prior release instead of
   letting it stand.

## v1.4.16 — 2026-07-10 — Triple Tax Calculus (docs-only)

1. First actual measurement of the "triple tax" claim instead of leaving it
   asserted — 4668.8x compiled-vs-raw ratio, reproducible.
2. Reported an honest falsification alongside the win: the pass-labeling
   probe self-reported 0 passes, not the claimed 3.
3. Fixed a real misattribution (draft mis-signed as Colombo, corrected to
   Codex) before it could propagate.

## v1.4.15 — 2026-07-10 — ARCHITECTURE.md full revision (docs-only)

1. Fixed a real diagram bug: showed a `DENIED` outcome that doesn't exist in
   `OutcomeKind`, replaced with the actual one (`ABSTAIN`).
2. Documented, for the first time, which of the 10 declared outcomes are
   actually reachable from real code (7 of 10) versus declared-but-unused.
3. Verified every diagram against live code via `run_verify`/`run_scenario`
   instead of just re-reading source.

## v1.4.14 — 2026-07-10 — FPF scope audit log + scope-rail reflection (docs-only)

1. Consolidates every external FPF pattern checked in one session into one
   categorized log — a direct answer instead of a commit-history search.
2. States a concrete self-imposed limit (never let this package's own size
   become something it has to manage) later releases can be held to.
3. Distinguishes inspected-and-confirmed from rejected from background
   awareness — three confidence levels, not a flat list.

## v1.4.13 — 2026-07-10 — E.20 awareness note (docs-only)

1. Rules out an external pattern as inapplicable (wrong actor, not wrong
   scope) with the reasoning recorded.
2. Keeps the external-references index complete instead of silently skipping
   something actually checked.
3. Zero functional change — pure paper-trail update, zero regression risk.

## v1.4.12 — 2026-07-10 — E.23 awareness note (docs-only)

1. Records a specific, verifiable reason a pattern doesn't apply (no agentic
   retry loop exists in the runtime path).
2. Prevents future contributors from re-proposing the same rejected idea
   unchecked.
3. Keeps the provenance trail complete without touching runtime code.

## v1.4.11 — 2026-07-10 — honest sourcing: remove overclaim, document SemanticFloor (docs-only)

1. Removes a false "nothing was invented" claim before it misleads an
   originality audit.
2. Adds three primitives already cited in code but missing from the summary
   table — closes a real doc/code mismatch.
3. Documents `SemanticFloor`'s 5-tier TTL structure as this package's own
   synthesis — accurate credit, neither over- nor under-claimed.

## v1.4.10 — 2026-07-10 — I.2 validation note (docs-only)

1. Records independent validation that a real design bet (compiling
   FPF-pattern selection once, by a human) holds up against an external annex.
2. Backfills a missing cross-link (the F.17 rejection) into the index.
3. Zero runtime risk — provenance-only update.

## v1.4.9 — 2026-07-10 — reject F.17 (out of scope) (docs-only)

1. Documents explicitly why an ecosystem-scale pattern doesn't apply to a
   single terminal package — stops the question being re-litigated later.
2. Points to where the equivalent need is already covered.
3. Keeps the rejection log complete and auditable.

## v1.4.8 — 2026-07-10 — external references index (docs-only)

1. Gives integrators one place to see what background material was reviewed,
   with one-line verdicts.
2. Explicitly marks all of it "not incorporated" — prevents assuming these
   references changed runtime behavior.
3. Zero functional risk.

## v1.4.7 — 2026-07-10 — link E.4.FPF carrier pattern (docs-only)

1. Records the specific normative pattern that classifies this package as a
   "carrier" — grounds a README claim in an actual citation.
2. Keeps `SOURCES.md` as a single accurate index of what's been checked.
3. No code touched, no regression risk.

## v1.4.6 — 2026-07-10 — related work: Miltonian/principles (docs-only)

1. Documents an independently-built parallel project reproducing this
   package's own thesis under a harder empirical standard.
2. Explicit "not incorporated, no code overlap" framing prevents assuming a
   merge or dependency that doesn't exist.
3. Keeps the provenance record honest about influence versus coincidence.

## v1.4.5 — 2026-07-09 — README title sync (docs-only)

1. Fixes README title/version footers left out of sync with the renamed
   repo.
2. Synced consistently across three files instead of leaving a half-fixed
   state.
3. Zero functional change — pure signage correction.

## v1.4.4 — 2026-07-09 — repo rename metadata sync (docs-only)

1. Updates `project_urls` to match the renamed repo — broken PyPI metadata
   links are a real integrator annoyance this closes.
2. Updates `SOURCES.md` to match, keeping the provenance trail consistent
   post-rename.
3. No functional change — pure metadata correction.

## v1.4.3 — 2026-07-08 — ADV-07: RiskAbove case-sensitivity silent failure

1. Documents a sharp real gotcha: `RiskAbove("critical")` silently treats
   `"CRITICAL"` (wrong case) as `"normal"` with no error.
2. Found via naive/careless-usage testing, closer to how a real integrator
   would actually trip it.
3. Confirmed with a concrete reproducible example wired exactly per the
   library's own recommended fix.

## v1.4.2 — 2026-07-08 — ADV-03..06

1. Documents the sharpest trust-model gap in the package: `active_context_id`
   is self-asserted and never verified against an actual bridge crossing.
2. Adds three more concrete authoring traps found by running real scenarios,
   not guesswork.
3. Frames every one as "library correctly declining to guess a policy
   decision," setting accurate expectations instead of implying a bug.

## v1.4.1 — 2026-07-08 — Advisories for integrators

1. Ships `ADVISORIES.md` — surfaces where the library stays deliberately
   minimal so integrators don't mistake a design boundary for an oversight.
2. Documents two concrete gotchas found by running a gold-test suite (expired
   evidence still satisfying `required_evidence`; `risk_level` not filtering
   `possible_transitions`).
3. `dev_mcp` gains `get_advisories()` so the same information is queryable,
   not just readable.

## v1.4.0 — 2026-07-08 — Stagnation counter

1. Closes a real blind spot: no prior way to notice "I've revisited this
   exact state N times with nothing new."
2. Purely additive — no new outcome kind, nothing newly blocked, zero
   behavior change for existing callers.
3. States its own limitation honestly (gameable by an evidence-inflating
   harness) instead of overselling the guarantee.

## v1.3.1 — 2026-07-06 — README scope-framing fixes (docs-only)

1. Corrects a real overclaim ("this package is the reasoning engine") that
   misrepresented what the library does.
2. Fixes two stale-doc bugs (install instructions predating PyPI
   availability; a version-footer mismatch) that would have actively misled
   a new user.
3. Fills a changelog gap — v1.3.0's real additions were otherwise
   undocumented.

## v1.3.0 — 2026-07-06 — Validated bridge crossing, lean slice reads

1. Cross-context bridge crossing is now actually enforced
   (`cross_bridge()`/`attempt_bridge()` refuse an unlicensed bridge under
   high/critical risk) instead of just describing the risk.
2. `include_full_state=False` lets a transition-focused caller get just the
   scoped slice instead of the whole board by default.
3. Default behavior unchanged — existing callers see no behavior change.

## v1.2.1 — 2026-06-27 — Agentic Thinking Map (PyPI debut)

1. Published on PyPI (`pip install fpf-thinking-map`) — removes the
   git+https install barrier.
2. Slice blockers explain *why* a move can't fire, not just that it can't.
3. Action-oriented vocabulary ("insufficient"/"denied" instead of "abstain")
   gives a clearer signal for a model deciding what to do next.

## v1.2.0 — 2026-06-27 — Agentic Thinking Map

1. TTL evidence decay (5 semantic floors, FGR-computed) gives the runtime a
   real, arithmetic notion of evidence going stale.
2. Structured response contract (claim, scope, basis, obligations, correct
   terms) in every slice — a consistent shape a calling model can rely on.
3. `IDLE`/`BRIDGE` outcomes give the traversal clean terminal and
   cross-context-escape states.

## v1.0.1 — 2026-06-24 — FPF source review statement and release

1. Publishes an explicit verdict against 6 real upstream FPF commits: confirms
   the design, no misunderstandings found — external validation, not
   self-assessment.
2. Names exactly what was adopted (A.15.5 Work-Entry Readiness, as a guard)
   versus rejected (C.32, NQD/OEE), with reasoning.
3. States the independent/MIT-licensed relationship to FPF explicitly, heading
   off any assumption of official affiliation.

## v1.0.0 — 2026-06-24 — Agentic Thinking Map (first release)

1. Compiles the FPF spec's 10 semantic primitives into a runnable package
   instead of leaving them as ~51k lines a model would have to re-derive
   every call.
2. Deterministic guards (9) and a traversal engine with 8 lawful outcomes —
   the actual mechanism that lets the runtime say "here's what's legal."
3. States a design rule from day one ("only add structure when it changes
   agentic behavior") that later releases can be held to.
