# FPF Agentic Thinking Map

**v1.4.25** — a compact runtime map for LLM agents.

Built from [FPF (First Principles Framework)](https://github.com/ailev/FPF) as a bounded traversal core: explicit state, lawful next move, inspectable outcomes.

Python 3.12+ · MIT · zero runtime dependencies

- [Visual architecture →](ARCHITECTURE.md)
- [Live demo →](https://igareosh.github.io/fpf-agentic-thinking-map/demos/)
- [Release history →](https://github.com/igareosh/fpf-agentic-thinking-map/releases)
- [Deep decisions/rejections/adoptions →](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)

---

## What this is

This map keeps agentic traversal clean.

It does **not** run heavy semantic payload inside the step loop.  
It does **not** force reasoning-on-reasoning recursion.  
It does **not** let traversal bloat with generated thinking trash.

The model stays free to generate.  
The map only keeps runtime state and checks the next lawful move.

---

## Why this exists

In long multi-step runs, models waste budget on self-management:

- re-checking what was already checked
- re-deriving state from prior prose
- re-arguing about their own prior reasoning

That is where drift and context noise come from.

This package moves traversal bookkeeping to code:

- context
- roles
- transitions
- evidence freshness
- guards and blockers
- outcome kind

So the model spends capacity on the task, not on traversal clutter.

---

## Runtime contract

Each step returns a compact JSON slice:

- where the agent is
- what can fire
- what is blocked
- what evidence is missing or stale
- what outcome applies

Outcomes include:

- `CONTINUE`
- `COLLECT_EVIDENCE`
- `BRIDGE`
- `IDLE`
- `ESCALATE`

The map constrains traversal legality.  
It does not overwrite user meaning and does not replace model intelligence.

---

## Measured per step

This was tested on **5 shipped decision points**.

- compiled `state.slice()` averaged **481.4 tokens per decision**
- raw FPF exact-section prompt averaged **138977.2 tokens per decision**
- that is **288.7x smaller per decision**
- in live billed input tokens, compiled averaged **537.4** vs raw **139194.6**
- that is a **259.0x** live per-decision input gap

Full measurement: [TRIPLE_TAX_CALCULUS.md](docs/deep/TRIPLE_TAX_CALCULUS.md)

---

## Scope

This package is intentionally narrow.

It is for:

- bounded, stepwise agent traversal
- clearer failure signals
- lower runtime noise
- inspectable behavior

It is not:

- full semantic ingestion of FPF
- a universal reasoning engine
- a replacement for application logic
- an in-engine memory/retrieval system (no embeddings/vector store inside this engine)

---

## Quick start

```bash
# Python 3.12+
python -m fpf_thinking_map.verify
python -m fpf_thinking_map.examples
```

Install:

```bash
pip install fpf-thinking-map
```

---

## Minimal usage

```python
from fpf_thinking_map import (
    SemanticMap,
    ContextPrimitive,
    RolePrimitive,
    TransitionPrimitive,
    GatePrimitive,
    GateCheck,
    RuntimeBinding,
    ThinkingMapTraversal,
)

sm = SemanticMap()
sm.register_context(ContextPrimitive("deploy", "Deploy Context"))
sm.register_role(RolePrimitive("owner", "Owner", "deploy"))
sm.register_gate(
    GatePrimitive(
        "release_gate",
        "Release Gate",
        "deploy",
        checks=[GateCheck("tests", "Green tests", required_evidence=["test_results"])],
    )
)
sm.register_transition(
    TransitionPrimitive(
        "ship",
        "Ship release",
        "deploy",
        "candidate",
        "released",
        required_evidence=["test_results"],
    )
)

engine = ThinkingMapTraversal(sm)
state = engine.build_active_state(
    RuntimeBinding(
        task="release",
        actor_role_ids=["owner"],
        active_context_id="deploy",
        current_evidence=["test_results"],
    ),
    current_state="candidate",
)
outcome = engine.step(state)
print(outcome.kind)  # CONTINUE / COLLECT_EVIDENCE / BRIDGE / IDLE / ESCALATE
```

The engine is domain-agnostic. You define your own contexts, evidence, gates, and transitions.

---

## Relationship to FPF

Based on [ailev/FPF](https://github.com/ailev/FPF) by Anatoly Levenchuk.  
Independent implementation, MIT-licensed, with further development rights.

FPF is the broad frame.  
This package is the compact runtime traversal tool.

---

## Design principles

- add structure only when behavior improves
- keep per-step payload small
- keep legality checks explicit
- keep model generation free
- optimize for inspectability

---

## Compatibility

Works with model families that can read structured JSON and follow constraints.
No model-specific prompt protocol is required by the engine itself.

---

## Deep technical notes (optional)

If you need theory, adoption/rejection rationale, and analysis provenance, use:

- [Decisions, rejections, adoptions index](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)

Mainstream docs stay focused on runtime behavior and integration.

---

## License

MIT. See [LICENSE](LICENSE).

---

*"All speech is vain and empty unless it be accompanied by action."* — Demosthenes
