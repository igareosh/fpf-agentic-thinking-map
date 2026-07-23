<p align="center">
  <img src="docs/assets/fpf-agentic-thinking-map-header.png" alt="FPF Agentic Thinking Map — Agent freedom. Explicit movement rules." width="100%" />
</p>

# FPF Agentic Thinking Map

FPF Agentic Thinking Map is a free, public, MIT-licensed Python runtime for
agent traversal.

It keeps the parts that must stay explicit in code: state, evidence freshness,
lawful transitions, authorization, waiting, and concrete move identity. The
model can still reason freely, but the runtime decides what move is actually
allowed.

**v1.9.1** · Python 3.12+ · zero runtime dependencies

[![PyPI version](https://img.shields.io/pypi/v/fpf-thinking-map?label=PyPI)](https://pypi.org/project/fpf-thinking-map/)
[![Python versions](https://img.shields.io/pypi/pyversions/fpf-thinking-map?label=Python)](https://pypi.org/project/fpf-thinking-map/)
[![License](https://img.shields.io/pypi/l/fpf-thinking-map?label=License)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-2ea44f)](pyproject.toml)
[![Verify](https://img.shields.io/badge/verify-26%2F26%20pass-2ea44f)](fpf_thinking_map/verify.py)
[![Live demo](https://img.shields.io/badge/demo-live-7c3aed)](https://igareosh.github.io/fpf-agentic-thinking-map/demos/)

---

## Install And Try

```bash
pip install fpf-thinking-map
python -m fpf_thinking_map.verify
python -m fpf_thinking_map.examples
```

```python
from fpf_thinking_map import (
    SemanticMap,
    ContextPrimitive,
    RolePrimitive,
    GatePrimitive,
    GateCheck,
    TransitionPrimitive,
    RuntimeBinding,
    ThinkingMapTraversal,
)

sm = SemanticMap()
sm.register_context(ContextPrimitive("deploy", "Deploy"))
sm.register_role(RolePrimitive("owner", "Owner", "deploy"))
sm.register_gate(
    GatePrimitive(
        "release_gate",
        "Release gate",
        "deploy",
        checks=[GateCheck("tests", "Tests are green", required_evidence=["test_results"])],
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

print(engine.step(state).kind)
```

The runtime is domain-agnostic. Replace the deployment vocabulary with your
own contexts, roles, evidence, gates, and transitions.

---

## Why It Exists

Long agent runs drift when the model has to keep reconstructing where it is,
what it may do next, and what still depends on outside input.

This package moves traversal bookkeeping into ordinary code:

- current context and state
- evidence presence and TTL freshness
- gates, guards, and lawful transitions
- human authorization
- external dependencies and wake conditions
- concrete move identity and trace lineage

That lets the model spend capacity on the task instead of on remembering the
workflow shape.

---

## AWAIT

`PendingInput` is the runtime's explicit "not done yet, but not lost" state.
It names an external dependency, such as a worker result or a human reply, and
describes the `wake_conditions` that would resolve it.

When nothing else is actionable and an unresolved `PendingInput` exists,
`step()` returns `AWAIT` instead of `IDLE`.

Important boundary:

- a candidate action still wins over waiting
- a context bridge still wins over waiting
- the runtime never polls, schedules, or resolves the dependency
- the host owns `PendingInput.status`

This keeps "waiting" separate from "finished."

---

## MoveIntent

`TransitionPrimitive` names a reusable move type. `MoveIntent` names one
concrete proposal.

That separation matters because one transition can be proposed many times with
different parameters or lineage. `MoveIntent` gives each proposal:

- a stable `move_id`
- optional `parent_move_id`
- opaque `parameters`

`ThinkingMapTraversal.inspect_move(state, intent)` checks a proposal without
firing it. `attempt_transition(state, transition_id, intent=...)` fires the
move and stamps trace lineage on success.

This keeps "what kind of move is this?" distinct from "which specific move
just happened?"

---

## Provenance

`AuthorizationReceipt`, `PendingInput`/`AWAIT`, and `MoveIntent` are separate
mechanisms with one shared purpose: they close gaps in what the runtime can
say about its own state.

Each one replaces a vague or overloaded shape with something inspectable:

- approval scoped to one transition and one inspected state
- waiting scoped to a declared external dependency
- movement scoped to one concrete proposal instead of a reusable transition

That is the line that keeps the runtime small, explicit, and honest.

Full narrative: [`EXPANDED_PROVENANCE.md`](docs/deep/EXPANDED_PROVENANCE.md)
· version-by-version: [`CHANGELOG.md`](CHANGELOG.md).

---

## What It Gives You

- Explicit state instead of prose memory.
- Evidence-aware transitions with freshness checks.
- Lawful next-move selection in code, not in narration.
- Human authorization for selected transitions.
- External waiting states that stay distinct from "done."
- Concrete move identity and trace lineage.

## What It Is Not

- A universal reasoning engine.
- A semantic ingestion system for all of FPF.
- An embeddings or vector database.
- A tool runner, queue, scheduler, or worker supervisor.
- A substitute for application-specific policy.

---

## Read Next

- [Architecture](ARCHITECTURE.md)
- [Release history](docs/VERSION_TRACKER.md)
- [Design decisions, rejections, and adoptions](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)
- [Integrator advisories](docs/deep/ADVISORIES.md)
- [Deep test harness](dev_mcp/README.md)

---

## Relationship To FPF

This project is inspired by [ailev/FPF](https://github.com/ailev/FPF) by
Anatoly Levenchuk.

It is an independent implementation with its own runtime scope. FPF provides
the broad conceptual frame; this package compiles the part that improves this
package's observable agent behavior.

---

## Documentation, Attribution, And Licence

- [NOTICE](NOTICE)
- [SHA256SUMS](SHA256SUMS)

**Maintained by:** igareosh.com · **Contact:** igareosh@igareosh.com ·
**GitHub / Telegram:** @igareosh

**Contributors:** igareosh · OpenAI Codex (README refinement)

This is a small community implementation: free to use, open to inspect, and
meant to be a practical point of discussion rather than a total framework.

**License:** MIT. See [LICENSE](LICENSE).
