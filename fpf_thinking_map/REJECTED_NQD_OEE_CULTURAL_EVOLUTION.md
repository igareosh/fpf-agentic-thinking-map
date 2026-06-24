# Rejected: NQD / OEE / Cultural Evolution patterns

**Status**: Rejected — will not be added to this package.
**Date**: 2026-06-24 (evaluation on 2026-06-22)
**Decision by**: igareosh (prichindel.com)
**FPF source sections**: C.17 (Creativity-CHR), C.18 (NQD-CAL), C.19 (E/E-LOG), A.4 (Open-Ended Evolution), B.5.2.1 (Creative Abduction with NQD)
**FPF repo**: [ailev/FPF](https://github.com/ailev/FPF)

---

## What these patterns are

- **NQD-CAL (C.18)**: Novelty–Quality–Diversity open-ended search calculus. Structured brainstorming, illumination-style emitters, portfolio coverage maps.
- **E/E-LOG (C.19)**: Explore–Exploit governor. Policy for balancing exploration and exploitation, exploration quotas, selection lenses.
- **OEE / Open-Ended Evolution (A.4, P-10)**: The principle that any holon is perpetually incomplete and can be improved. Design-time vs run-time evolution.
- **Creativity-CHR (C.17)**: Characterizing generative novelty and value — Novelty, Use-Value, Surprise, Constraint-Fit scoring.
- **Creative Abduction (B.5.2.1)**: Hypothesis generation bound to NQD search with diversity maintenance.

These are interesting in FPF-land. They are not current-core for this thinking map.

## Why they are rejected

Same class of risk as C.32 (candidate-synthesis), documented in `REJECTED_C32_CANDIDATE_SYNTHESIS.md`. The reasoning applies identically:

### These patterns are bias injectors

NQD/OEE/cultural evolution material is:
- **Search-front expanding** — it widens the space of considered options
- **Novelty-seeking** — it rewards divergence from known paths
- **Diversity-maintaining** — it resists convergence toward a single answer
- **Portfolio-multiplying** — it turns one decision into a set of tracked alternatives

Base LLMs already over-index on these behaviors. They generate options readily, branch eagerly, and resist committing to a single path. These are deep training priors, not learned from FPF.

If the thinking map encodes NQD/OEE patterns, it does not add neutral semantic structure. It **amplifies existing model habits** toward exploration, divergence, and candidate multiplication — exactly the behaviors a per-move constrained map should not encourage.

### The thinking map is convergent, not divergent

| This package | NQD/OEE/cultural evolution |
|-------------|---------------------------|
| Narrows to one move | Expands to a search front |
| Guards block invalid moves | Exploration quotas keep options open |
| Evidence must be present | Novelty is rewarded for being new |
| Transitions are bounded | Evolution is open-ended |
| Convergent per step | Divergent by design |

### The design rule

> Only add structure when a missing relation changes what the agent does on a single move.

NQD/OEE patterns do not constrain a move. They generate and maintain alternative moves. They expand the per-step chew instead of reducing it. Wrong direction.

## What to do instead

If novelty/diversity/search-front behavior is explicitly needed for a domain:
- It belongs in a **separate strategy module** outside the thinking map
- The thinking map evaluates and constrains moves that arrive from that module
- The map itself stays neutral — it does not invite the model to explore

The map is a **guard rail**, not a **search engine**.

---

prichindel.com | 2026-06-24 | v1.0.0
