# prichindel.com Agentic Thinking Map

**v1.0.1** — [FPF (First Principles Framework)](https://github.com/ailev/FPF) compiled into a semi-formal thinking map for agentic AI guidance.

A Python package that gives an AI model a small, structured board to reason on — one move at a time. Instead of freeform text generation, the model navigates a pre-shaped semantic field with deterministic guards and propositional logic constraints.

## What it does

You define a domain as a semantic map (contexts, roles, gates, evidence, transitions). The model gets a per-move slice — just the current transition, its gate, its evidence, and whether it can fire. Deterministic guards enforce hard constraints the model cannot override. Propositional logic rules (NOT, AND, OR, XOR, IMPLIES, IFF) provide decision glue between the semantic primitives and the model's reasoning.

The model's job is not "what does FPF mean?" — it is: **given this semantic map and this state, what is the best lawful next move?**

## Quick start

```bash
# No dependencies. Python 3.12+.

# Verify the package (12 checks)
python -m fpf_thinking_map.verify

# Run the deploy decision scenario
python -m fpf_thinking_map.example_scenario

# Run the logic operators scenario
python -m fpf_thinking_map.example_logic_scenario
```

## Package contents

```
fpf_thinking_map/
├── primitives.py             10 semantic objects from FPF spec
├── state.py                  SemanticMap + RuntimeBinding + ActiveState + slice()
├── guards.py                 9 deterministic guards (context, role, gate, evidence, assignment, speech act, readiness)
├── logic.py                  6 logic operators + decision rules + LogicLayer
├── traversal.py              Step engine with 8 lawful outcomes
├── verify.py                 Self-verification harness (12/12 checks)
├── example_scenario.py       Deploy decision walkthrough
├── example_logic_scenario.py Logic operators in action + truth table
├── README.md                 Full documentation (any-model readable)
├── SOURCES.md                Source attribution (FPF spec + Mitev lectures)
├── FPF_SOURCE_TO_CODE_RELATION_AUDIT.md   50-item relation audit
├── FPF_AUDIT_RESPONSE.md     Audit response with design decisions
├── REJECTED_C32_CANDIDATE_SYNTHESIS.md    C.32 rejection (activation bias)
└── REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md NQD/OEE rejection (bias injector)
```

## Relationship to ailev/FPF

This package is built on [ailev/FPF](https://github.com/ailev/FPF) by Anatoly Levenchuk. It is an independent implementation — our own research and code, MIT-licensed, with further development rights.

### What we reviewed

We cross-checked the following FPF commits (June 2026 precision restoration cluster) against our code:

- [`20c8a0a`](https://github.com/ailev/FPF/commit/20c8a0a) — ontic, declarative algorithms, method-work cleanup
- [`205de76`](https://github.com/ailev/FPF/commit/205de76) — role and method ontic refactoring
- [`cf12b97`](https://github.com/ailev/FPF/commit/cf12b97) — U-kinds+ontics normalization
- [`fe0df9d`](https://github.com/ailev/FPF/commit/fe0df9d) — holons and meta-holon transition normalization
- [`3becd8e`](https://github.com/ailev/FPF/commit/3becd8e) — MOVE precision restoration
- [`b74ecf2`](https://github.com/ailev/FPF/commit/b74ecf2) — move disambiguation full corpus scan

**Verdict**: the FPF precision restoration confirms our existing design choices rather than contradicting them. His semantics got closer to what we already built.

### What we adopted

One item passed our scope filter:

- **A.15.5 Work-Entry Readiness** — "is everything ready to even start this work?" is a different question from "does the gate pass?" Added as `readiness_refs` on transitions, enforced as a guard condition. Thin enough to be a guard, not a new primitive.

### What we rejected

Two FPF pattern families rejected for activation bias — they amplify existing LLM priors instead of constraining them:

- **C.32 Candidate-Synthesis Logic** ([`10cd224`](https://github.com/ailev/FPF/commit/10cd224cef9c92043fb6821e165decd6ea05073f)) — variant racing, tradeoff-seeking, candidate-multiplying. These are motion patterns, not neutral semantic relations. See [REJECTED_C32_CANDIDATE_SYNTHESIS.md](fpf_thinking_map/REJECTED_C32_CANDIDATE_SYNTHESIS.md).
- **NQD/OEE/Cultural Evolution** (C.17–C.19, A.4) — novelty-seeking, diversity-maintaining, search-front expanding. Same activation bias class. See [REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md](fpf_thinking_map/REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md).

**Design rule**: the map evaluates and constrains moves. It does not propose them. Generative, branch-friendly, candidate-multiplying patterns are the opposite of what a per-move guard-constrained thinking map should contain.

## Sources

- **[FPF (First Principles Framework)](https://github.com/ailev/FPF)** by Anatoly Levenchuk — transdisciplinary specification (~51k lines). We extracted 10 semantic primitives and 9 guard rules. This is a compiled distillation, not a port.
- **Computational logic (Mitev L.)** — "Bazele programarii logice." 6 propositional logic operators and the Wumpus World agent navigation pattern.

Full attribution in [SOURCES.md](fpf_thinking_map/SOURCES.md).

## Design principles

- **Only add structure when it changes agentic behavior** — not for source fidelity alone
- **Per-step chew = one move slice** — never context feast
- **Horizontal operational clarity** over vertical semantic completeness
- **Compile-time richness** over runtime payload growth

## Compatibility

Built with Claude Code (Anthropic claude-sonnet-4-6). Tested and verified to work with:

| Model family | Status | Notes |
|-------------|--------|-------|
| **Anthropic Claude** (Sonnet, Opus, Haiku) | Works | Built and tested here. Slice size fits comfortably in context. |
| **OpenAI GPT** (GPT-4o, o1, o3) | Works | Used for the 50-item source-to-code relation audit. Reads the primitives, logic rules, and prompt state correctly. |
| **Any model that reads JSON and follows structured constraints** | Should work | The package outputs plain dicts. No model-specific prompting. |

This is not a compliance seal. It means: we used these models against this package and they produced correct, usable results. The per-move slice is small enough for mid-tier models. The logic and guard outputs are plain JSON — no special tokenization or prompt format required.

## License

MIT. See [LICENSE](LICENSE).

---

**prichindel.com** — v1.0.1 — 2026-06-24
