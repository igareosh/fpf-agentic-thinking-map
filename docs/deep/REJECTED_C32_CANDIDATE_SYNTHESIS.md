# Rejected: C.32 Candidate-Synthesis Logic

**Status**: Rejected — will not be added to this package.
**Date**: 2026-06-24
**Decision by**: igareosh (prichindel.com)
**FPF source**: [ailev/FPF commit 10cd224](https://github.com/ailev/FPF/commit/10cd224cef9c92043fb6821e165decd6ea05073f)

---

## What C.32 is

C.32 in the FPF spec introduces candidate-synthesis logic: structured option generation, variant racing, tradeoff-seeking, and candidate-multiplying patterns for decision-making under uncertainty.

## Why it is rejected

This package is a **neutral semantic scaffold** — a thinking map that constrains an LLM's per-move reasoning within bounded semantics. C.32 material would break that neutrality.

### The core problem: activation bias

The base models (GPT, Claude, Gemini, etc.) already contain strong priors for option generation. They are trained to branch, propose alternatives, weigh tradeoffs, and multiply candidates. These are deep model habits, not learned from FPF.

If the thinking map encodes C.32 patterns — even lightly — it stops being a neutral scaffold and becomes a **behavioral trigger**. The model does not just "have access" to candidate-synthesis logic. It starts to feel **invited to branch**, because the map mirrors priors the model already over-selects for.

The result:
- The map amplifies existing model habits instead of constraining them
- The model over-selects "variant racing" even when the scope is narrow and the move is clear
- The map stops preserving source semantics and becomes a **remapping layer** that biases toward generative branching

### C.32 material is especially dangerous for a thinking map because it is:

- **Generative** — it produces options, not constraints
- **Branch-friendly** — it rewards divergence, not convergence
- **Tradeoff-seeking** — it opens evaluation dimensions instead of closing them
- **Candidate-multiplying** — it expands the decision space instead of narrowing it

These are **motion patterns**, not neutral semantic relations. They are the opposite of what a per-move guard-constrained thinking map should contain.

### The design rule applies

> Only add structure when a missing relation changes what the agent does on a single move.

C.32 does not constrain a move. It multiplies moves. That is the wrong direction for this package.

### What belongs here vs what does not

| This package | C.32 material |
|-------------|--------------|
| One move at a time | Many candidates at once |
| Guards constrain invalid moves | Synthesis generates more moves |
| Slice narrows the decision space | Variant racing widens it |
| Deterministic checks | Generative exploration |
| Convergent | Divergent |

The thinking map's value is that it makes each step **smaller and more bounded**. C.32 makes each step **larger and more open**. These are incompatible directions.

## What to do instead

If candidate-synthesis is needed for a specific domain, it belongs in the **LLM prompt layer** or in a separate **strategy module** that runs outside the thinking map. The thinking map evaluates and constrains moves that have already been proposed — it does not propose them.

---

prichindel.com | 2026-06-24 | v1.0.0
