# Related work: miltonian/principles

**Status**: Acknowledged — independent parallel work, not incorporated, not a shared source.
**Date**: 2026-07-10
**Decision by**: igareosh (prichindel.com)
**Related repo**: [miltonian/principles](https://github.com/miltonian/principles)
**Author's writeup**: [OpenAI Community — Principles Framework: generate AI agents using first-principles reasoning](https://community.openai.com/t/principles-framework-generate-ai-agents-using-first-principles-reasoning/1045890)

---

## What we found

A "Principles Framework" by Alexander Hamilton (miltonian) — a TypeScript pipeline, built on the Claude Agent SDK, that takes a goal and generates a team of specialized agents by applying first-principles decomposition: survey the landscape, derive typed "truths," adversarially vet each one (a skeptic tries to kill it), decompose into subtasks against a coverage map, judge the decomposition against a rubric, refine, then run a separate frame-level skeptic that can reject the whole frame as solving the wrong problem.

No shared lineage with this package. This package compiles Levenchuk's FPF spec (see `SOURCES.md`); `principles` does not reference FPF and was built independently, from OpenAI Swarm and a multi-agent-systems essay as its stated influences. Two unrelated projects converging on "first principles" as the operating name — worth recording so nobody assumes one derives from the other.

Full respect for the effort, in particular the part most projects in this space skip: a real controlled benchmark (`benchmarks/research-pilot/`) comparing the bare model against the compiled pipeline on Scale AI's ResearchRubrics, graded by a different model family to avoid home-team bias, with predictions pre-registered in writing before the final run and losses reported alongside wins. That is a materially higher evidence bar than most "framework improves LLM output" claims ship with.

## What the benchmark actually shows

Their first version of the compiled pipeline *lost* to the bare model — 0.552 vs 0.653 mean score — because structure without a verified synthesis step degraded the final render (wrong format, leaked scaffolding text, truncated output). Three more iterations (synthesis contract + gates, deliverable framing, then grounded framing with a frame-level skeptic and a specificity-retention gate) were needed before the compiled pipeline beat bare: 0.698 vs 0.653, winning 7 of 9 tasks. Stage-attribution on the transcripts found ~80% of lost weight in an intermediate version was decided at the truths step, before any downstream check could catch it.

That v1 result is an independent, empirical confirmation of this package's own `WHY_THIS_EXISTS.md` thesis from a completely different architecture and author: bolting a first-principles framework onto a model's reasoning path, unverified, does not just fail to help — it actively degrades output, and the damage is concentrated wherever nobody thought to add a check.

## Where the designs diverge

`principles` keeps the model doing framework-driven reasoning at every stage, and fixes the failure mode by adding adversarial skepticism and grounding around that reasoning — an LLM call per stage, judged and refined until it converges. This package removes the model from framework-reasoning entirely: FPF is compiled once, at build time, into a small deterministic engine, and the model receives a precomputed JSON slice at runtime with zero framework-reasoning calls in the loop (see `RELATED_WORK_GOFLOW_FPF_SKILL.md` for the same divergence against a different independent project).

Two valid answers to the same observed failure — verify the model's use of the framework at every step, or remove the model from framework-reasoning so there is nothing to verify at runtime. Nothing from `principles` was pulled into this package; there is no code overlap. This note exists to record that we are aware of it, that it independently reproduces our core finding under a harder empirical standard than we hold ourselves to, and that the effort deserves the credit for doing so.

---

prichindel.com | 2026-07-10 | v1.4.5
