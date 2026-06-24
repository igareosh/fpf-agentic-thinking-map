# prichindel.com Agentic Thinking Map

**v1.0.0** — [FPF (First Principles Framework)](https://github.com/ailev/FPF) compiled into a semi-formal thinking map for agentic AI guidance.

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
├── guards.py                 9 deterministic guards (context, role, gate, evidence, assignment, speech act)
├── logic.py                  6 logic operators + decision rules + LogicLayer
├── traversal.py              Step engine with 8 lawful outcomes
├── verify.py                 Self-verification harness (12/12 checks)
├── example_scenario.py       Deploy decision walkthrough
├── example_logic_scenario.py Logic operators in action + truth table
├── README.md                 Full documentation (any-model readable)
├── SOURCES.md                Source attribution (FPF spec + Mitev lectures)
├── FPF_SOURCE_TO_CODE_RELATION_AUDIT.md   50-item relation audit
└── FPF_AUDIT_RESPONSE.md     Audit response with design decisions
```

## Sources

- **[FPF (First Principles Framework)](https://github.com/ailev/FPF)** by Anatoly Levenchuk — transdisciplinary specification for reasoning, assurance, and evolution (~51k lines, "operating system for thought"). We extracted 10 semantic primitives and 9 guard rules from the FPF spec. This package is a compiled distillation for agentic use, not a port of the full framework. The original spec and its Python tooling live in the [ailev/FPF](https://github.com/ailev/FPF) repository.
- **Computational logic (Mitev L.)** — university lecture series "Bazele programarii logice" (Fundamentals of Logic Programming). 6 propositional logic operators (NOT, AND, OR, XOR, IMPLIES, IFF) and the Wumpus World agent navigation pattern adopted from lectures c1p–c5p.

Full attribution with spec-section-to-code mapping in [SOURCES.md](fpf_thinking_map/SOURCES.md).

## Design principles

- **Only add structure when it changes agentic behavior** — not for source fidelity alone
- **Per-step chew = one move slice** — never context feast
- **Horizontal operational clarity** over vertical semantic completeness
- **Compile-time richness** over runtime payload growth

## License

MIT. See [LICENSE](LICENSE).

---

**prichindel.com** — v1.0.0 — 2026-06-24
