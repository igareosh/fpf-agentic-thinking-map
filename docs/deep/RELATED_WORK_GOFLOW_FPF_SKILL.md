# Related work: goflowspace/goflow FPF skill

**Status**: Acknowledged — independent prior art, not incorporated.
**Date**: 2026-06-30 (discovered 2026-06-29)
**Decision by**: igareosh (prichindel.com)
**Related repo**: [goflowspace/goflow](https://github.com/goflowspace/goflow/tree/main/.claude/skills/fpf)
**FPF source repo**: [ailev/FPF](https://github.com/ailev/FPF)

---

## What we found

An independent decomposition of Levenchuk's FPF specification, published as a Claude Code skill at `goflowspace/goflow/.claude/skills/fpf/`. Both projects derive from the same source — FPF-Spec.md, ~51,000 lines — with no mutual awareness, and arrived at opposite designs.

Full respect for the effort: 189 pattern files across 11 domains, roughly 3.7 MB of structured reference material, plus maintenance tooling (`fpf_tools.py`, `split_fpf_spec.py`, `audit_fpf_patterns.py`) to search and audit the corpus. It is free, public, and a serious piece of decomposition work. This note exists to record what it is, what we evaluated from it, and why none of it was pulled in here — not to diminish it.

## What goflow built

A **prompt-time reference library**. The model reads pattern markdown at inference time, evaluates its own position against natural-language criteria written into the patterns, and picks the next branch. Progressive disclosure (master index → domain index → pattern file) keeps token cost down. It is a skill, not an engine — there is no code that evaluates state and returns a verdict; the model is the evaluator.

## What this package builds

A **runtime constraint engine**: 10 primitives, 9 deterministic guards, 6 propositional logic operators, one traversal loop. The model never evaluates its own reasoning state. It receives a state snapshot, the engine checks deterministic facts (evidence present, gate passed, role conflict, freshness), and returns one of eight fixed outcomes. The model navigates a board with walls; it does not judge the quality of its own thinking.

## Coverage comparison

| Domain | goflow patterns | This package |
|---|---|---|
| foundations (A.0–A.19) | 20 | 10 primitives |
| transformation (A.3–A.15, B.4) | 14 | WorkPrimitive, WorkPlanPrimitive |
| reasoning (B.5–B.7) | 8 | — |
| trust-evidence (A.10, B.3, C.2) | 12 | EvidencePrimitive + FGR |
| aggregation (B.1–B.2) | 15 | — |
| signature (A.6) | 17 | ContextBridge only |
| architheories (C.1–C.25) | 46 | — |
| constitution (E.1–E.20) | 30 | — |
| unification (F.0–F.18) | 20 | — |
| ethics (D.5) | 2 | — |
| sota (G.0–G.13) | 16 | — |

goflow covers roughly 5x the specification surface. That is the correct outcome for a reference library and the wrong direction for a constraint engine — see `WHY_THIS_EXISTS.md` on the compiled-vs-raw tax this package is built to avoid.

## The core design disagreement

goflow's skill is a prompt-time reference the model reads, self-evaluates against, and uses to steer its own reasoning. The model asks itself "am I in Explore or Shape?", answers itself, and picks the next branch. The patterns are decision trees the model walks by interpreting natural-language criteria written into the pattern text.

This package is the opposite. The model does not self-evaluate. The engine evaluates state and returns a verdict; the model gets an `Outcome` it can act on. The model navigates, the guards constrain. No self-assessment, anywhere in the loop.

Two valid designs for different problems. goflow trusts the model to be an honest judge of its own reasoning state. We don't.

We also don't think we need to. This package has never had to put a model in the position of reasoning about its own reasoning — and reasoning-about-reasoning is exactly where models hallucinate most confidently. A model asked "what kind of thinking am I doing right now" will answer fluently and wrongly with equal ease; there is no way to check the answer against anything external. The map's job is to give the model a board to walk and walls it cannot walk through — not to ask it to grade the quality of its own thought, which is the one judgment call it cannot be trusted to make honestly.

## Patterns evaluated and rejected

### B.5.1 — Explore → Shape → Evidence → Operate (ESEO)

Considered adding a `ReasoningPhase` enum to `ActiveState` (EXPLORE / SHAPE / EVIDENCE / OPERATE) with a guard enforcing phase order, mirroring goflow's lifecycle pattern.

**Rejected.** Phase assignment requires the model to answer "am I in Explore or Shape?" — a self-evaluative claim with no externally checkable answer. A guard that validates this claim is circular: it constrains a fact only the constrained party can report. It also forks the decision into three branches before any guard runs, which is the wrong direction for a package designed to converge to one move per step (same objection as `REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md`).

What ESEO actually prescribes — no operating without evidence, no skipping the shaping step — is already enforced by the existing guards:

- `commitment_evidence` — blocks proceeding without required evidence
- `planning_not_enactment` — blocks marking done without work records
- `gate_pass` — blocks skipping a structural checkpoint
- `evidence_freshness` — flags stale evidence

The lifecycle is implicit in the guard composition already shipped. Making it explicit adds an enum, a state field, a constraint, and a guard — four new moving parts to formalize something the guards already do, with no new failure mode caught.

### B.5 — Canonical Reasoning Cycle (Abduction → Deduction → Induction)

Considered a reasoning-mode selector mirroring the three-phase cycle.

**Rejected.** Whether the model is abducting, deducing, or inducing is a property of its internal process, not of the observable state this engine evaluates (evidence, gates, transitions, roles). There is no state-layer signal to check it against. Adding the selector buys three-way ambiguity per step with no verification path — exactly the failure mode this package exists to avoid (per `WHY_THIS_EXISTS.md`).

### A.3.1 / A.3.2 — Method vs. MethodDescription split

goflow keeps the design-time recipe (MethodDescription) and the runtime-bound instance (Method) as separate patterns. This package's `WorkPrimitive.method_id` collapses both.

**Not rejected, deferred.** Legitimate split — would add one intermediate state and one guard ("no Work without a bound Method"). Held back because no observed failure mode in current usage needs it. First candidate to revisit if method-binding bugs show up.

## Conclusion

Same source, opposite bets on what a model can be trusted to do with its own introspection. goflow trusts the model to grade its own reasoning state against reference text. This package doesn't, and routes every decision through external, deterministic checks instead. Nothing from goflow's decomposition was pulled into this package. The guard stack already does, implicitly, what the rejected patterns would have made explicit — without asking the model to self-report.

---

prichindel.com | 2026-06-30 | v1.2.1
