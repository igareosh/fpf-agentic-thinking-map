# Rejected: F.17 Unified Term Sheet

**Status**: Rejected — will not be added to this package.
**Date**: 2026-07-10
**Decision by**: igareosh (prichindel.com)
**FPF source**: [fpf.sh/generated/patterns/F.17](https://fpf.sh/generated/patterns/F.17)

---

## What F.17 is

F.17 is a governance pattern in Part F (The Unification Suite) for publishing a **Unified Term Sheet**: a reader-facing table that lets multiple teams reuse the same term names across different bounded contexts without guessing what each other meant. Every row carries a governed object/value, its direct governing pattern, bounded-context-and-edition-scoped local senses, cross-context bridge references (F.9), Tech and Plain names (F.5/F.18), admissible and blocked use, a row edition, and a currentness condition — nine conformance rules (`UTS-SCR-01..09`) in total.

## Why it is rejected

F.17 solves a coordination problem that only exists at ecosystem scale: many independent downstream projects (DPFs) minting overlapping names and needing a shared table so, say, two different `ReviewerRole` uses don't silently collide. This package is not that. It is a single, terminal, compiled artifact — ten primitives, nine guards, six logic operators, one repository, one edition. There is no second bounded context inside this package for a term to drift across, and this package does not publish names for other projects to build on top of.

We already have the lightweight version of the thing F.17 protects against ambiguity on: the "What we took from FPF and where it is in the spec" table in `SOURCES.md`. It maps every primitive (`RolePrimitive`, `GatePrimitive`, etc.) to its direct FPF section and what that section means — the same recovery-mechanism idea F.17 formalizes, sized for ten primitives in one package instead of a whole ecosystem of teams.

### Pattern that doesn't apply at this scope

Adopting full UTS machinery — row IDs, blocks, Tech/Plain name splits, per-row admissible/blocked use, per-row currentness conditions — would formalize something already implicit and working, buying process weight without catching any failure mode this package has actually hit. Same shape of rejection as `REJECTED_C32_CANDIDATE_SYNTHESIS.md` and the ESEO pattern in `RELATED_WORK_GOFLOW_FPF_SKILL.md`: structure added for its own sake, not because a missing relation changes what the model does on a single move.

## What would change this

If this package ever spawns multiple downstream forks independently reusing its primitive names in incompatible ways, that is the trigger to revisit — not a rejection reversed outright, but a "not rejected, deferred" case, the same treatment the Method/MethodDescription split got in `RELATED_WORK_GOFLOW_FPF_SKILL.md`.

---

prichindel.com | 2026-07-10 | v1.4.8
