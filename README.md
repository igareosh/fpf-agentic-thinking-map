<p align="center">
  <img src="docs/assets/fpf-agentic-thinking-map-header.png" alt="FPF Agentic Thinking Map — Agent freedom. Explicit movement rules." width="100%" />
</p>

# FPF Agentic Thinking Map

FPF Agentic Thinking Map is a free, public, MIT-licensed Python runtime for
multi-step agent traversal.

It keeps the pieces that should stay explicit in code: state, evidence
freshness, lawful transitions, authorization, and waiting conditions. The
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

## What Problem It Solves

In long multi-step agent runs, models can lose track of what was already
checked, what is still valid, and what move is lawful next. Prose instructions
compete with task content, earlier decisions, tool output, and context
compression.

This package moves traversal bookkeeping into ordinary code:

- current context and state
- evidence presence and TTL freshness
- gates, guards, and lawful transitions
- cross-context bridges
- human authorization
- external dependencies and wake conditions
- concrete move identity and trace lineage

This is not another reasoning prompt. It is a compact control surface around
reasoning.

---

## Runtime Flow

```text
Application / Agent
        │
        ▼
   RuntimeBinding
        │
        ▼
    ActiveState
        │
        ├── evidence freshness
        ├── gate checks
        ├── transition legality
        └── authorization
        │
        ▼
      Outcome
CONTINUE | COLLECT_EVIDENCE | BRIDGE | IDLE | ESCALATE
```

`step()` returns a compact JSON slice: where the agent is, what can fire,
what is blocked, what evidence is missing or stale, and which outcome applies.
The map constrains traversal legality. It does not overwrite user meaning and
does not replace model intelligence.

---

## Core Capabilities

- **Explicit state** - contexts, roles, and the active state are first-class
  objects, not prose the model has to re-derive each turn.
- **Evidence gates** - transitions declare `required_evidence`; the engine
  checks freshness before it lets a move fire.
- **Lawful transitions, enforced in code** - the legality of the next move is
  computed outside the token stream, so it cannot be silently reinterpreted
  the way prose instructions can.
- **Inspectable outcomes** - every step resolves to one of a fixed set of
  outcome kinds, not free text.

---

## Ignition Lock And Abort To Orbit

`requires_human_authorization` lets a transition be fully legal by every
FPF-computed measure and still refuse to fire without caller approval.
`safe_alternatives` plus `ActiveState.deny_pending_authorization(...)` mean a
denial can reroute to a declared non-destructive twin instead of dead-ending.

`AuthorizationReceipt` scopes approval to one transition and the exact state
it was issued against. `attempt_transition(..., authorization=receipt)`
rejects it if the transition, state, expiry, or prior consumption do not
match.

- [`ADOPTED_IGNITION_LOCK.md`](docs/deep/ADOPTED_IGNITION_LOCK.md) - what
  shipped, why, and how it was tested
- [`ADVISORIES.md`](docs/deep/ADVISORIES.md) - integrator advisories and known
  sharp edges
- [`run_scenario_destructive_hitl` / `run_scenario_denied_reroute`](fpf_thinking_map/examples.py)
  - runnable walkthroughs
- [`dev_mcp`](dev_mcp/README.md) - test your own map against the live engine

---

## AWAIT

`PendingInput` declares an external dependency - a worker result, a human
reply, anything the map itself does not produce - with `wake_conditions`
describing what would resolve it. When nothing else is actionable and an
unresolved `PendingInput` exists, `step()` returns `AWAIT` instead of `IDLE`.

A candidate action or a context bridge still wins over waiting. The map never
polls, schedules, or resolves the dependency; the host owns that lifecycle and
updates `PendingInput.status` itself.

---

## MoveIntent

`TransitionPrimitive` names a reusable move type. `MoveIntent` gives one
concrete proposal a stable `move_id`, optional lineage, and a place for its
own parameters to live.

`ThinkingMapTraversal.inspect_move(state, intent)` evaluates one proposal
without firing anything. `attempt_transition(state, transition_id, intent=...)`
fires exactly as before and stamps trace lineage on success.

---

## Provenance

`AuthorizationReceipt`, `PendingInput`/`AWAIT`, and `MoveIntent` are separate
mechanisms with one throughline: each closes a gap in what the runtime can say
about its own state, instead of flattening that into a bare boolean, a bare
string, or a single overloaded rest state.

Full narrative: [`EXPANDED_PROVENANCE.md`](docs/deep/EXPANDED_PROVENANCE.md)
· version-by-version: [`CHANGELOG.md`](CHANGELOG.md).

---

## Measurements

Tested on **5 shipped decision points**:

- compiled `state.slice()` averaged **481.4** tokens per decision
- raw FPF exact-section prompt averaged **138977.2** tokens per decision
- that is **288.7x smaller** per decision

This measures traversal-context size for these five decision points - compiled
runtime state versus injecting the equivalent raw FPF source sections - not
general model intelligence or total application cost. Full methodology:
[`TRIPLE_TAX_CALCULUS.md`](docs/deep/TRIPLE_TAX_CALCULUS.md).

---

## Architecture And Repository Components

- [Visual architecture](ARCHITECTURE.md) - core engine
- [dev_mcp visual architecture](dev_mcp/ARCHITECTURE.md) - MCP tool layer
- `fpf_thinking_map/` - published runtime library, what PyPI ships
- `dev_mcp/` - development and compliance-testing harness
- `docs/` - architecture, experiments, decisions, and adversarial studies
- [Release history](https://github.com/igareosh/fpf-agentic-thinking-map/releases)
- [Design decisions, rejections, and adoptions](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)
- [Related projects we've reviewed](docs/RELATED_PROJECTS.md)
- [Live demo](https://igareosh.github.io/fpf-agentic-thinking-map/demos/)

---

## Relationship To FPF

This project is inspired by [ailev/FPF](https://github.com/ailev/FPF) by
Anatoly Levenchuk.

It is an independent implementation with its own runtime scope. FPF provides
the broad conceptual frame; this package compiles the part that improves this
package's observable agent behavior.

---

## Scope And Non-Goals

It is for:

- bounded, stepwise agent traversal
- clearer failure signals
- lower runtime noise
- inspectable behavior
- human authorization where needed
- clean separation between waiting, resting, and acting

It is not:

- full semantic ingestion of FPF
- a universal reasoning engine
- a replacement for application logic
- an in-engine memory or retrieval system
- a tool runner, scheduler, or worker/task supervisor

Compatibility: it works with model families that can read structured JSON and
follow constraints. No model-specific prompt protocol is required by the
engine itself.

---

## Documentation, Provenance, Attribution, And Licence

- [Decisions, rejections, adoptions index](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)
- [Integrator advisories](docs/deep/ADVISORIES.md)
- [SHA256SUMS](SHA256SUMS)
- [NOTICE](NOTICE)

**Maintained by:** igareosh.com · **Contact:** igareosh@igareosh.com ·
**GitHub / Telegram:** @igareosh

**Contributors:** igareosh · OpenAI Codex (README refinement)

This is a small community implementation: free to use, open to inspect, and
meant to be a practical point of discussion rather than a total framework.

**License:** MIT. See [LICENSE](LICENSE).
