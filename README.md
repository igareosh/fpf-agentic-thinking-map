<p align="center">
  <img src="https://raw.githubusercontent.com/igareosh/fpf-agentic-thinking-map/main/docs/assets/fpf-agentic-thinking-map-header.png" alt="FPF Agentic Thinking Map - Agent freedom. Explicit movement rules." width="100%" />
</p>

# FPF Agentic Thinking Map

A small, deterministic Python runtime for agents that may reason freely but
must move through a workflow lawfully.

It keeps operational state, evidence freshness, transition legality,
authorization boundaries, and waiting conditions outside the model's prose
context. The model can inspect the map and choose; the runtime decides whether
the move is valid.

[![PyPI](https://img.shields.io/pypi/v/fpf-thinking-map?style=flat-square&label=PyPI&color=3775A9)](https://pypi.org/project/fpf-thinking-map/)
[![Downloads (honest)](https://img.shields.io/badge/downloads%20%28honest%29-3.8k-1f6feb?style=flat-square)](https://pypistats.org/packages/fpf-thinking-map)
[![Python](https://img.shields.io/pypi/pyversions/fpf-thinking-map?style=flat-square&label=Python&color=f0b429)](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![License](https://img.shields.io/pypi/l/fpf-thinking-map?style=flat-square&label=license&color=57c7bd)](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-ff9f43?style=flat-square)](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![Verification](https://img.shields.io/badge/verify-26%2F26-59d18c?style=flat-square)](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/fpf_thinking_map/verify.py)
[![Live demo](https://img.shields.io/badge/live-demo-dd8cff?style=flat-square)](https://igareosh.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

```bash
pip install fpf-thinking-map
python -m fpf_thinking_map.verify
```

## Important links

- [ARCHITECTURE.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/ARCHITECTURE.md)
- [VERSION_TRACKER.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md)
- [TRIPLE_TAX_CALCULUS.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/TRIPLE_TAX_CALCULUS.md)
- [REFLECTIONS.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/REFLECTIONS.md)
- [CONTRIBUTING.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/CONTRIBUTING.md)
- [ADVISORIES.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md)
- [`dev_mcp/`](https://github.com/igareosh/fpf-agentic-thinking-map/tree/main/dev_mcp)

The `dev_mcp` development and compliance harness is genuinely tested against
the package and updated whenever runtime behavior, compliance checks, or
integration requirements change.

## The problem

An agent can explain a workflow rule and still lose track of it during a long
run. Prose instructions compete with task content, earlier decisions, tool
output, and context compression.

FPF Agentic Thinking Map moves the parts that should not depend on narration
into ordinary code:

- current context and state;
- evidence presence and TTL freshness;
- gates, guards, and lawful transitions;
- cross-context bridges;
- human authorization;
- external dependencies and wake conditions;
- concrete move identity and trace lineage.

This is not another reasoning prompt. It is a compact control surface around
reasoning.

## The contract

The division of responsibility is deliberate:

| Agent or application | Thinking map runtime |
| --- | --- |
| Interprets the task | Holds explicit traversal state |
| Generates and compares options | Computes which moves are legal |
| Collects evidence | Checks presence and freshness |
| Proposes a concrete move | Inspects or attempts that move |
| Explains the result | Returns a bounded outcome and trace |
| Requests human input | Enforces the authorization boundary |
| Executes tools and jobs | Never executes, polls, or schedules them |

The map constrains movement, not meaning. It does not replace the model,
application logic, retrieval, tools, or a task scheduler.

## Live runtime visual

[![Three test-backed traces of the traversal runtime](https://raw.githubusercontent.com/igareosh/fpf-agentic-thinking-map/main/docs/assets/three-runs-preview.png)](https://igareosh.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

**[Open the interactive three-run trace](https://igareosh.github.io/fpf-agentic-thinking-map/demos/three-runs.html)**

The visual follows evidence recovery, `PendingInput`/`AWAIT`, `MoveIntent`,
state-bound authorization, and successful traced movement in the current
runtime.

## Minimal example

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

semantic_map = SemanticMap()
semantic_map.register_context(ContextPrimitive("deploy", "Deploy"))
semantic_map.register_role(RolePrimitive("owner", "Owner", "deploy"))
semantic_map.register_gate(
    GatePrimitive(
        "release_gate",
        "Release gate",
        "deploy",
        checks=[
            GateCheck(
                "tests",
                "Tests are green",
                required_evidence=["test_results"],
            )
        ],
    )
)
semantic_map.register_transition(
    TransitionPrimitive(
        "ship",
        "Ship release",
        "deploy",
        "candidate",
        "released",
        required_evidence=["test_results"],
    )
)

traversal = ThinkingMapTraversal(semantic_map)
state = traversal.build_active_state(
    RuntimeBinding(
        task="release",
        actor_role_ids=["owner"],
        active_context_id="deploy",
        current_evidence=["test_results"],
    ),
    current_state="candidate",
)

inspection = traversal.step(state)
result = traversal.attempt_transition(state, "ship")

print(inspection.kind)
print(result.kind)
print(state.current_state)
```

The map is domain-agnostic. Replace the deployment vocabulary with your own
contexts, roles, evidence, gates, and transitions.

Run the packaged scenarios:

```bash
python -m fpf_thinking_map.examples
```

## What is enforced

### Explicit state

The active position is a first-class object, not a conclusion the model must
repeatedly reconstruct from chat history.

### Evidence with age

Transitions can require evidence. Evidence can decay by semantic floor and
TTL, allowing the runtime to distinguish present evidence from usable
evidence.

### Gates, guards, and logic

Gates test declared conditions. Guards enforce hard constraints. A small
propositional layer composes facts without asking the model to reinterpret the
rules on every step.

### Validated bridges

Cross-context movement is explicit. High-risk substitution without a
sufficient bridge contract is refused or escalated rather than silently
treated as equivalent.

### Human authorization

`requires_human_authorization` separates "structurally legal" from "authorized
to execute."

For stronger integrations, `AuthorizationReceipt` binds approval to:

- one transition;
- the exact inspected state fingerprint;
- an expiry boundary;
- single consumption.

A denied move may expose declared `safe_alternatives`, so escalation does not
have to become a dead end.

### External waiting

`PendingInput` and `AWAIT` distinguish "the workflow is finished" from "the
workflow is alive but waiting for something outside the map." The host owns
polling and resolution.

### Concrete move identity

`MoveIntent` distinguishes a reusable transition type from one particular
proposed move. `inspect_move()` evaluates it without mutation; a successful
transition can stamp move lineage into the trace.

## Why the versions matter

The project has grown by closing specific ambiguities in traversal state, not
by expanding into a general agent framework.

| Release line | Capability added |
| --- | --- |
| v1.0 | Runnable semantic primitives, deterministic guards, lawful traversal |
| v1.2 | Evidence TTL, response contracts, `IDLE` and `BRIDGE` |
| v1.3 | Enforced bridge crossing and lean state slices |
| v1.4 | Stagnation detection, integrator advisories, verified documentation |
| v1.5 | Stable public package boundary |
| v1.6 | Human authorization and safe denial routes |
| v1.7 | State-bound, expiring authorization receipts |
| v1.8 | External dependency tracking and `AWAIT` |
| v1.9 | Concrete move identity, inspection, lineage, authorization-clock fix |

The complete reader-facing history is in
[docs/VERSION_TRACKER.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md).
Technical changes are in
[CHANGELOG.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/CHANGELOG.md),
and full release bodies remain in
[GitHub Releases](https://github.com/igareosh/fpf-agentic-thinking-map/releases).

This separation is intentional: the README describes the stable product; the
tracker records how that product became stronger.

## Evidence, verification, and limits

The repository includes three different kinds of support. They should not be
confused:

- Deterministic verification checks runtime invariants directly.
- Scenario and adversarial tests exercise integration behavior and known
  failure shapes.
- Model experiments show behavior under stated conditions; they are evidence,
  not universal guarantees.

```bash
python -m fpf_thinking_map.verify
python -m fpf_thinking_map.examples
```

The compiled state slice was also measured against injecting the corresponding
raw FPF sections at five shipped decision points. The measured slice was much
smaller, but this is a traversal-context result, not a claim about general
intelligence or total application cost. Method and limitations:
[TRIPLE_TAX_CALCULUS.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/TRIPLE_TAX_CALCULUS.md).

For the authorization experiments, threat boundaries, failures found, and
claims deliberately not made, see
[IGNITION_LOCK_WIND_TUNNEL.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/IGNITION_LOCK_WIND_TUNNEL.md).

## Scope

Use this library when you need:

- bounded multi-step traversal;
- explicit next-move legality;
- evidence-aware workflow state;
- inspectable reasons for blocking or escalation;
- human authorization for selected transitions;
- a clean distinction between waiting, resting, and acting;
- compact state projections for an LLM or agent host.

Do not use it as:

- a universal reasoning engine;
- a semantic ingestion system for all of FPF;
- an embeddings or vector database;
- a tool runner, queue, scheduler, or worker supervisor;
- a substitute for application-specific policy;
- a certification that an entire agent system is safe.

Correct map authoring and correct host integration remain part of the trust
boundary. Known sharp edges and deliberate non-goals are recorded in
[ADVISORIES.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md).

## Repository guide

| Path | Purpose |
| --- | --- |
| [`fpf_thinking_map/`](https://github.com/igareosh/fpf-agentic-thinking-map/tree/main/fpf_thinking_map) | Zero-dependency runtime published to PyPI |
| [`dev_mcp/`](https://github.com/igareosh/fpf-agentic-thinking-map/tree/main/dev_mcp) | Separate development and compliance-testing harness |
| [ARCHITECTURE.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/ARCHITECTURE.md) | Verified control flow and module architecture |
| [docs/VERSION_TRACKER.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md) | Every release, with three practical consequences |
| [docs/DECISIONS_REJECTIONS_ADOPTIONS.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/DECISIONS_REJECTIONS_ADOPTIONS.md) | Design provenance and rejected scope |
| [docs/deep/ADVISORIES.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md) | Integration boundaries and known sharp edges |
| [SHA256SUMS](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/SHA256SUMS) | Repository-wide source fingerprints |

## Design rules

1. Keep the model free to generate and compare.
2. Keep movement legality explicit and deterministic.
3. Add structure only when it changes observable behavior.
4. Keep each decision payload small.
5. Keep host responsibilities outside the core.
6. Record rejected ideas as carefully as adopted ones.
7. Prefer a narrow mechanism with inspectable limits over a broad claim.

## Relationship to FPF

This project is inspired by [ailev/FPF](https://github.com/ailev/FPF) by
Anatoly Levenchuk. It is an independent, MIT-licensed implementation with its
own runtime scope.

FPF provides the broad conceptual frame. This package compiles a selected part
of that frame into a practical traversal runtime. It may omit or reject
patterns that do not improve this package's observable agent behavior.

See [NOTICE](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/NOTICE)
and [SOURCES.md](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/docs/deep/SOURCES.md)
for attribution and scope boundaries.

## License and contact

MIT License. See
[LICENSE](https://github.com/igareosh/fpf-agentic-thinking-map/blob/main/LICENSE).

Maintained by [igareosh.com](https://igareosh.com) ·
[@igareosh](https://github.com/igareosh) ·
[igareosh@igareosh.com](mailto:igareosh@igareosh.com)

**Agent freedom. Explicit movement rules.**
