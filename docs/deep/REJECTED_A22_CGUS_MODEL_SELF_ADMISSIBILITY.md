# Rejected: A.22.CGUS as a model self-admissibility procedure

**Status**: Acknowledged as a real FPF pattern — rejected as a practice for this package.
**Date**: 2026-07-17
**Decision by**: igareosh (prichindel.com)
**FPF source**: `A.22.CGUS` — Constraint-Governed Unfolding Structure, added to [ailev/FPF](https://github.com/ailev/FPF) 2026-07-09 (post-dates our 2026-06-24 vendoring snapshot; not yet a row in `SOURCES.md`)

---

## What A.22.CGUS is

A specialization of `A.22` (Structure and Structural Views), opened only when a candidate structure has several loci and cross-locus constraints — disqualified for anything that's just a simple chain. Its discipline is a three-way separation:

1. **Provisional demonstration** — a readable walkthrough/example chain shown *before* the full structure is admitted as a CGUS. Showing one path is not a claim that the graph exists.
2. **Post-admission whole-structure description** — once admitted, the entire thing: branches, joins, cycles, alternatives, cross-position constraints, admissible next-forms, stop/return conditions.
3. **Post-admission demonstrative slice** — a selected traversal walked for a reader after admission (`F.17`'s "demonstrative walkthrough" / "mantra move").

The point of `A.22.CGUS` is to stop a single happy-path example — a README diagram, a seminar mantra, one chain of steps — from quietly standing in for the real structure with all its branches and constraints. It is a **documentation/authoring discipline**: it governs how you're allowed to *describe* a structure once it exists or is claimed. It says nothing about how admissible next-forms get generated or selected.

## The practice evaluated and rejected

The practice under evaluation: using CGUS's "admissible next-forms" vocabulary to frame an LLM agent enumerating candidate decisions (e.g. "generate 10 options, pick one") as if the enumeration were a genuine search and the pick a considered admissibility judgment.

**Rejected**, for the same shape of reason `RELATED_WORK_GOFLOW_FPF_SKILL.md` rejected `ESEO`: it asks the model to grade something only the model itself can report, with no externally checkable answer.

Concretely: autoregressive generation conditions on everything already written, including the model's own prior tokens. Once a model has started listing candidate options, each subsequent option — and the eventual pick — is generated *consistent with* what it already said, not independently re-derived. The "deliberation" is compiled in one pass; the enumeration is post-hoc scaffolding dressed up as process. A weak Nth option can get waved through purely because the accumulated context already leans toward approving it — sycophancy / in-context anchoring, not adjudication. The longer the visible reasoning chain, the more the model optimizes for coherence with itself over correctness. Same circularity already on record: *"the constraint validates a claim that only the constrained entity can make."*

`A.22.CGUS` does not cause this failure mode and does not claim to fix it — it is silent on generation and selection entirely. The rejection is of the practice that borrows its vocabulary to imply a safety property it doesn't grant.

## The requirement this sharpens

Not a new gap in this package's design — a sharpening of the bet already made in `RELATED_WORK_GOFLOW_FPF_SKILL.md`: **any admissibility verdict must come from outside the agentic LLM runtime that is narrating the decision.** Concretely, that means one of:

- a genuinely separate model/agent invoked fresh, with no shared conversation history — nothing to be sycophantic *toward*; or
- a non-LLM device: deterministic code, a fixed rule evaluator, with no next-token-coherence pressure to rubber-stamp anything.

"The same model steps back and self-critiques in the next paragraph" does not satisfy this — it still conditions on the same accumulated context and inherits the same anchoring bias. It is not a second opinion; it is an echo.

This package's guard stack already is the second kind: plain Python evaluating state records (evidence present, gate status, role conflict, freshness), zero LLM calls in the runtime path. That is exactly why it cannot be talked into approving a weak option regardless of how much prior context leans that way. If the enumerating model were ever allowed to also compute its own admissibility verdict, that would quietly swap the deterministic guard for "the model self-reports which of its imagined options it likes" — same theater, FPF vocabulary on top.

## What would change this

If `A.22.CGUS` (or a later specialization of it) is ever adopted here purely as a **naming/documentation** convention — to describe our traversal engine's own branch structure for human audit, with no claim about how a model selects among branches — that is not this rejection reversed, it's a different, narrower use that never touches runtime trust. First candidate to revisit if we formalize that documentation, not before.

---

prichindel.com | 2026-07-17 | v1.5.0
