> "Pick something. Get good at it. See if you can be the best at it." — Jordan Peterson

# FPF Agentic Thinking Map

**v1.5.0** — a compact runtime map for LLM agents.

Built from [FPF (First Principles Framework)](https://github.com/ailev/FPF) as a bounded traversal core: explicit state, lawful next move, inspectable outcomes.

Python 3.12+ · MIT · zero runtime dependencies

Published as a small community implementation: free to use, open to inspect,
and meant to be a practical point of discussion rather than a total framework.

## At a glance

[![PyPI version](https://img.shields.io/pypi/v/fpf-thinking-map?label=PyPI)](https://pypi.org/project/fpf-thinking-map/)
[![Python versions](https://img.shields.io/pypi/pyversions/fpf-thinking-map?label=Python)](https://pypi.org/project/fpf-thinking-map/)
[![License](https://img.shields.io/pypi/l/fpf-thinking-map?label=License)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-2ea44f)](pyproject.toml)
[![Verify](https://img.shields.io/badge/verify-23%2F23%20pass-2ea44f)](fpf_thinking_map/verify.py)

[![Live demo](https://img.shields.io/badge/demo-live-7c3aed)](https://igareosh.github.io/fpf-agentic-thinking-map/demos/)
[![Per decision](https://img.shields.io/badge/per%20decision-288.7x%20smaller-2ea44f)](docs/deep/TRIPLE_TAX_CALCULUS.md)
[![Traversal](https://img.shields.io/badge/traversal-no%20semantic%20bloat-111827)](#what-this-is)
[![Runtime shape](https://img.shields.io/badge/runtime-JSON%20slice%20per%20step-1f6feb)](#runtime-contract)

Badges above describe the **core engine** (`fpf_thinking_map/`, what PyPI ships).
`dev_mcp/` is separate dev-only tooling for agentic testing against that engine —
not shipped, own test suite, own count, on purpose kept distinct rather than
folded into the numbers above:

[![dev_mcp self-test](https://img.shields.io/badge/dev__mcp%20self--test-31%2F31%20pass-1f6feb)](dev_mcp/test_server.py)
[![dev_mcp compliance mode](https://img.shields.io/badge/dev__mcp-compliance%20mode-1a3a5c)](dev_mcp/compliance_inspector.py)
[![dev_mcp advisories](https://img.shields.io/badge/integrator%20advisories-9-8b6914)](docs/deep/ADVISORIES.md)

- [Visual architecture →](ARCHITECTURE.md) (core engine)
- [dev_mcp visual architecture →](dev_mcp/ARCHITECTURE.md) (MCP tool layer, testing mode)
- [Live demo →](https://igareosh.github.io/fpf-agentic-thinking-map/demos/)
- [Release history →](https://github.com/igareosh/fpf-agentic-thinking-map/releases)
- [Deep decisions/rejections/adoptions →](docs/DECISIONS_REJECTIONS_ADOPTIONS.md)
- [Related projects we've reviewed →](docs/RELATED_PROJECTS.md) (not used by us, not a partnership — just noted so we don't forget)

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

## Why this isn't another prompt

Most agent setups today handle this with prose: a CLAUDE.md, a system prompt,
a rules file telling the model to behave. That's still just tokens sitting in
context, waiting to be silently deprioritized or reinterpreted as the
conversation grows.

This package doesn't ask the model to remember discipline, it removes the
need for discipline. Legality of the next move is computed in code
(`GatePrimitive`, `TransitionPrimitive`, required evidence) — outside the
token stream, so it can't be silently reinterpreted the way prose
instructions can be. That's a structural difference, not a wording
difference.

---

## Human-in-the-loop for destructive moves

Full-autonomy agentic runs are normal now — an agent frames a problem,
collects evidence, and drives itself state to state without a human reading
every step. Most of that traversal, this map is happy to let through: gates
pass, evidence is fresh, fire.

Destructive and irreversible moves are the exception, and the FPF logic
underneath doesn't get more cautious about them on its own. If
`delete_records` has its required evidence and its gate is satisfied, the
traversal is legal and says `CONTINUE` — same as any other move. That's
correct behavior: the map has no built-in notion that deleting something is
different from deploying something. It shouldn't have to — that distinction
belongs to a separate layer, not baked into every gate.

`requires_human_authorization` is that layer — the field name says exactly
what it checks, on purpose: there's no bundled system prompt telling the
model what this flag means, so the name has to carry that on its own when
the model reads it cold in a `step()`/`slice()` response. Mark a transition
`requires_human_authorization=True` and the engine keeps computing and
reporting its legality — evidence and gate status are still shown in full —
it just refuses to fire without `authorized=True`, enforced at
`ActiveState.transition_to()` itself, so there's no lower-level call that
skips it. The model can see the delete is ready. It cannot pull the trigger.

**Where that "yes" comes from matters.** `authorized` is a plain argument —
nothing inside this engine stops a caller with direct access to it from
setting `authorized=True` on its own. This library has no identity system and
isn't getting one; that boundary is the integration's job, not the engine's.
Wiring it correctly means whatever harness sits around this engine — an MCP
server, a CLI, a chat approval step — never exposes `authorized` as something
the model's own tool-calling loop can set for itself. It has to come from a
channel the agent can request but not answer on its own behalf: a human
typing a confirmation, a separate approval endpoint, an explicit "yes / go".

**The waiting itself is a fact worth keeping, not just the refusal.**
`current_state="ready_to_restart"` looks identical whether a human is
mid-decision on `delete_records` or nobody's touched it yet — that's the gap
[`ADV-08`](docs/deep/ADVISORIES.md) already flags for this engine generally,
sharpened here. `ActiveState.pending_authorization` names the specific
transition a human is being asked about the moment `requires_human_authorization`
escalates, and it survives past that one call: it's a plain constructor
field, not one of the private counters `ADV-08` warns about, so a harness
restoring state after a restart can pass it straight back in. It's cleared
automatically the moment that *same* transition fires authorized — firing
something unrelated in the meantime does not erase it, and `step()` keeps
surfacing a warning about it regardless of which move is in view, so the
still-open ask doesn't quietly fall out of context. If the ask goes stale —
the model moved on, the question no longer applies — call
`resolve_pending_authorization()`. Nothing here assumes "pending" always
resolves to "yes".

See [`run_scenario_destructive_hitl`](fpf_thinking_map/examples.py) for the
full walk: evidence present, gate passing, still refused until authorized.

## When a human says no

A denial is a fact, not a dead end. Escalating for every destructive move
regardless of whether a legitimate non-destructive path existed too would be
its own failure — the exact shape of denying a database wipe for reasons
nobody could see, because nothing about the alternative was ever visible.

`TransitionPrimitive.safe_alternatives` names a transition's non-destructive
twins — explicit, declared, the same way `incompatible_with` and
`bridges_to` already work in this codebase. Never inferred: two transitions
merely sharing a `from_state` are not assumed to be substitutes for each
other. `slice()` surfaces them before the model ever attempts the destructive
move, and the `ESCALATE` `Outcome` carries them again if it does — so the
option is visible at the point of decision, not just discovered after a
refusal.

`ActiveState.deny_pending_authorization(transition_id, reason)` records an
explicit "no" — distinct from the stale-ask case above. It doesn't
permanently lock the door (a human can change their mind; a later
`authorized=True` still fires), but any retry's `ESCALATE` reason names what
was said before, so it's never silently re-asked as if nothing happened. It
also doesn't pick an alternative for you — the engine names the safe twin,
the model chooses to fire it, through the same ordinary `attempt_transition()`
as any other move. Whether the archive is actually an adequate substitute for
the delete is a domain judgment this library can't make; making sure that
judgment has something visible to work with is what it's for.

See [`run_scenario_denied_reroute`](fpf_thinking_map/examples.py): the same
escalation, this time denied with a reason, then resolved by firing the
declared alternative directly — destructive denied, task still done.

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
- HITL gating on destructive/irreversible transitions (`requires_human_authorization`),
  with declared non-destructive alternatives (`safe_alternatives`) so a denial
  routes somewhere instead of dead-ending

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
Acknowledged as inspiration and source material, not as a scope lock.

This package is an independent implementation, MIT-licensed, and open to
reuse in other developments. It keeps its own runtime scope and, where
needed to preserve that scope, omits or explicitly rejects parts of FPF
rather than inheriting the framework as an inseparable whole.

FPF is the broad frame.  
This package is the compact runtime traversal tool.

---

## Community and attribution

- Maintained by: **igareosh.com**
- Contact: **igareosh@igareosh.com**
- GitHub / Telegram: **@igareosh**
- Inspiration acknowledged: **Anatoly Levenchuk / `ailev/FPF`**

Plain-language attribution and scope boundaries live in
[NOTICE](NOTICE).

---

## Provenance

Repository-wide SHA-256 fingerprints live in [SHA256SUMS](SHA256SUMS).
They give a simple integrity proof for the tracked source state that
ships with this repository.

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

Testing this package's behavior against the documented [integrator
advisories](docs/deep/ADVISORIES.md) (evidence staleness, risk-level
filtering, bridge trust, and the rest)? [`dev_mcp`](dev_mcp/README.md) checks
scenario runs against all 8 automatically and keeps a log of what fired —
useful if you're integrating this into your own agent and want to know
which sharp edges your scenarios actually touched, not just which ones exist
on paper.

Mainstream docs stay focused on runtime behavior and integration.

---

## License

MIT. See [LICENSE](LICENSE).

For ownership, attribution, and scope notes, see [NOTICE](NOTICE).

---

*"All speech is vain and empty unless it be accompanied by action."* — Demosthenes
