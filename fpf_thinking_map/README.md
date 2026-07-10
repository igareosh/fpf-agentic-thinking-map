# FPF Thinking Map

This folder contains a Python package that helps an AI model make bounded decisions step by step. It combines a compiled subset of FPF with basic logic operations from computer science so the model can read a small move board instead of digesting a large framework at runtime.

No external dependencies. Pure Python 3.12+. No pip install needed.

## What problem this solves

When you give an AI model a question like "should we deploy this release?", the model can answer anything. It might forget to check if tests passed. It might skip asking for approval. It might say "deploy" and "collect more evidence" in the same breath.

This package gives the model a small, structured board to reason on. The board has:
- facts about the current situation (what evidence exists, what gates are open)
- rules about what is allowed (you cannot deploy without approval)
- logic checks that are deterministic (the model cannot override them)

The model reads the board, then picks from a fixed set of moves: continue, ask, abstain, escalate, collect evidence, etc.

The point is not to make the model "more intelligent." The point is to make its behavior smaller, more understandable, and less likely to drift for ordinary, inspectable reasons.

## Why this package exists next to FPF

FPF is strong material for humans, but too large to hand to a model raw and expect clean operational behavior. A model tends to absorb the vocabulary, imitate the posture of rigor, and still miss the simple thing it needed to do.

So we did not port the whole framework. We extracted what was useful for bounded traversal, made it executable, and left out the parts that would inflate runtime payload or trigger open-ended academic-pattern generation. This package is not "FPF but more." It is "the part of FPF that helps agents behave better, compiled into something they can actually use."

## Where this comes from

Two sources, both real academic material:

**Source 1: [FPF (First Principles Framework)](https://github.com/ailev/FPF)**
- A transdisciplinary specification (~51,000 lines) by Anatoly Levenchuk — "operating system for thought"
- It defines how to structure reasoning about systems: what roles exist, what evidence is needed, what gates must pass, how to transition between states
- We did NOT copy the whole spec. We extracted 10 objects from it and turned them into Python dataclasses
- The full spec lives in the [ailev/FPF](https://github.com/ailev/FPF) repository

**Source 2: Computational logic lectures (Mitev L.)**
- 5 lecture PDFs on propositional logic from a university course
- "Bazele programarii logice" (Fundamentals of Logic Programming)
- 5 lecture PDFs (c1p through c5p) — not included in this repository
- We took the 6 basic logic operators (NOT, AND, OR, XOR, IMPLIES, IFF) and built them as Python classes that evaluate against the current state
- The key pattern we adopted is from lecture 5: the Wumpus World. An agent navigates a grid, uses propositional logic to determine which cells are safe. Same idea here — the model navigates semantic states, uses logic to determine which moves are safe

## What is in each file

```
fpf_thinking_map/
│
├── primitives.py            10 semantic objects + 5 semantic floors from FPF
├── state.py                 Binding, state, TTL tracking, evidence status, slice
├── guards.py                9 deterministic guards the model cannot break
├── logic.py                 6 logic operators + EvidenceFresh + decision rules
├── traversal.py             Step engine with 10 lawful outcomes (incl. IDLE, BRIDGE)
├── verify.py                Self-test: run it, if 22/22 pass, package works
│
├── examples.py              5 deploy decision scenarios (all features in action)
│
├── __init__.py              Package exports
├── README.md                This file
└── SOURCES.md               Detailed source attribution
```

## The 10 objects from FPF (primitives.py)

These are Python dataclasses. Each one was extracted from a specific section of the FPF spec. v1.1: includes SemanticFloor (5 vertical levels) and FGR-modulated TTL decay.

| Object | What it is | Plain example |
|--------|-----------|---------------|
| `ContextPrimitive` | A bounded area where words have specific meanings | "Project Delivery" context where "deploy" means "push to production" |
| `RolePrimitive` | A role someone plays in a context, with conflicts | "Analyst" role — cannot also be "Approver" (separation of duties) |
| `WorkPrimitive` | A record of something planned or actually done | "Deployment plan" (plan) vs "Deployment executed at 3pm" (enactment) |
| `CommitmentPrimitive` | A rule: MUST, SHOULD, or MAY do something | "MUST have test results before deploying" |
| `GatePrimitive` | A checkpoint with pass/degrade/abstain outcome | "Deployment gate" — checks if tests passed AND approval obtained |
| `EvidencePrimitive` | A piece of evidence with a trust score (F-G-R) | "Test results from CI pipeline" — formality: 0.8, reliability: 0.9 |
| `TransitionPrimitive` | A move from one state to another, may require a gate | "ready_for_decision → deploying" requires deploy_gate to pass |
| `PublicationPrimitive` | A way to show results to an audience | "Assurance view for stakeholders" — only available after gate passes |

## The 6 logic operators (logic.py)

These are the standard logic operators from computer science. They evaluate to true or false against the current state.

| Operator | Symbol | What it checks | Example |
|----------|--------|---------------|---------|
| NOT | ¬ | The opposite | `NOT(evidence exists)` → true when evidence is missing |
| AND | ∧ | Both must be true | `tests_pass AND approval_obtained` → true only when both exist |
| OR | ∨ | At least one true | `rollback_plan OR not_at_deploy` → true if either holds |
| XOR | ⊕ | Exactly one true | `analyst XOR approver` → true when exactly one role is active |
| IMPLIES | → | If A then B | `gate_blocked IMPLIES gaps_exist` → false only when gate is blocked but no gaps |
| IFF | ↔ | Both same value | `ready_state IFF gate_passes` → true when both true or both false |

These get composed into `DecisionRule` objects. Each rule has:
- a `name`
- a `condition` (composed from the operators above)
- an `action_if_true` and optional `action_if_false`
- a `kind`: block, warn, route, or hint
- `tags` for filtering (so you can evaluate only "deploy" rules, or only "roles" rules)
- `exclusive_with` for contradiction detection

Rules are collected in a `LogicLayer` and evaluated together. The layer checks for consistency (no contradictory actions firing at the same time).

## The 9 guards (guards.py)

These are hard constraints. The model cannot override them. If a guard says DENY, the action is blocked.

| Guard | What it prevents |
|-------|-----------------|
| `commitment_evidence` | You cannot claim a MUST commitment is met without the evidence it requires |
| `planning_not_enactment` | Having a plan does not mean the work is done — cannot transition to "done" without enactment records |
| `role_conflict` | Two incompatible roles cannot be active at the same time (e.g., analyst and approver) |
| `gate_pass` | If a transition requires a gate and the gate abstains (insufficient evidence), the transition is blocked |
| `scope_check` | You cannot act in another context without an explicit bridge between contexts |
| `evidence_freshness` | Stale or TTL-expired evidence triggers a warning (uses floor-based decay) |
| `context_invariants` | Context invariants are surfaced as warnings for the model to consider |
| `expired_assignment` | Expired role assignments cannot authorize new work |
| `speech_act_validity` | Expired or revoked speech acts (approvals, authorizations) trigger denial |

Each guard has a `GuardScope` (TRANSITION, ROLE, EVIDENCE, or GLOBAL). The engine can evaluate only guards relevant to a specific move.

## How a step works (traversal.py)

```
Input: an ActiveState (context + role + evidence + current position)
       optionally: a specific transition_id to focus on

1. Check: is there an active context? If not → CHANGE_FRAME
2. Evaluate logic rules (filtered by tags if given)
   - If rules contradict each other → ABSTAIN
3. Run guards (scoped to the transition if given)
   - If any guard says DENY and evidence is missing → COLLECT_EVIDENCE
   - If any guard says DENY and no evidence path → ABSTAIN
4. Check for missing evidence on current transitions
   - If gaps exist → COLLECT_EVIDENCE
5. Check if transitions exist from current state
   - If actions available → CONTINUE
   - If bridges available → BRIDGE (cross-context escape)
   - If nothing → IDLE (at rest, not stuck)
   - If transitions available → CONTINUE

Output: an Outcome with:
  - kind: continue / ask / abstain / escalate / publish / revise_plan / collect_evidence / change_frame / idle / bridge
  - reason: why this outcome
  - missing_evidence: what is needed (if applicable)
  - warnings: non-blocking issues
  - llm_prompt_state: the JSON the model reads to decide its next move
```

When `transition_id` is given, the model gets a `slice()` — a tiny dict with just the move, its gate, its evidence, and whether it can fire. That is the per-move maneuver board. If the caller wants it, the package can now return that lean slice without bolting the full state back on.

## How state works (state.py)

Three objects:

**SemanticMap** — the static board. You register all your primitives here once. It does not change during a run.

**RuntimeBinding** — the input variables for one question/task. Includes:
- `task`, `goal`, `actor`
- `actor_role_ids` — which roles are active (must be explicitly listed, not inferred)
- `active_context_id` — which context we are in
- `current_evidence` — what evidence is available right now
- `risk_level` — low / normal / high / critical
- `candidate_actions`, `constraints`, `available_tools`, `audience`

**ActiveState** — the live state. Combines the map + binding + current position. Properties:
- `active_roles` — only roles that match both the binding AND the active context (no cross-context leakage)
- `possible_transitions` — only transitions in the active context from the current state
- `missing_evidence_for(transition_id)` — what this specific move needs that we don't have
- `slice(transition_id)` — tiny dict for one move
- `transition_to(transition_id)` — execute a transition (checks context, evidence, and gates)

**MoveTrace** — compressed history. Only stores last move, not full history: previous_state, last_transition_id, bridge_target, blockers, evidence_delta.

## Boundary rules (enforced, not advisory)

These constraints are checked at execution time, not just in the display layer:

1. **A transition from context B cannot execute when context A is active.** Both `attempt_transition()` and `transition_to()` check context match.
2. **A transition with `required_evidence` cannot execute if that evidence is missing.** Both `attempt_transition()` and `transition_to()` enforce this.
3. **Bound roles are validated against the active context.** A role from context B will not appear in `active_roles` when context A is active.
4. **Risk-sensitive logic rules are skipped at normal/low risk.** Only evaluated when risk is high or critical.

## How to run

```bash
# From the repo root:

# Verify the package works (21 checks)
python -m fpf_thinking_map.verify

# Run the deploy decision scenario
python -m fpf_thinking_map.examples
```

All three should run without errors. `verify` exits 0 on success, 1 on failure.

## How to build a new domain

Step 1: Create a `SemanticMap` and register your primitives.

```python
from fpf_thinking_map.state import SemanticMap, RuntimeBinding
from fpf_thinking_map.primitives import (
    ContextPrimitive, RolePrimitive, GatePrimitive, GateCheck,
    EvidencePrimitive, TransitionPrimitive, Freshness, FGR,
)

sm = SemanticMap()
sm.register_context(ContextPrimitive(
    context_id="my_domain",
    label="My Domain",
    glossary={"review": "check code for correctness"},
))
sm.register_role(RolePrimitive("reviewer", "Reviewer", "my_domain"))
sm.register_gate(GatePrimitive("review_gate", "Review Gate", "my_domain", checks=[
    GateCheck("tests", "Tests must pass", required_evidence=["test_results"]),
]))
sm.register_transition(TransitionPrimitive(
    "start_to_reviewed", "Start → Reviewed", "my_domain",
    from_state="start", to_state="reviewed",
    required_gate_id="review_gate",
    required_evidence=["test_results"],
))
```

Step 2: Optionally create logic rules.

```python
from fpf_thinking_map.logic import (
    LogicLayer, DecisionRule, RuleKind,
    EvidencePresent, GatePasses,
)

logic = LogicLayer()
logic.add_rule(DecisionRule(
    name="review_ready",
    condition=EvidencePresent("test_results").AND(GatePasses("review_gate")),
    action_if_true="proceed_to_review",
    action_if_false="not_ready",
    kind=RuleKind.ROUTE,
    tags=["review"],
))
```

Step 3: Create the engine and run a step.

```python
from fpf_thinking_map.traversal import ThinkingMapTraversal

engine = ThinkingMapTraversal(sm, logic_layer=logic)
binding = RuntimeBinding(
    task="review PR #42",
    actor_role_ids=["reviewer"],
    active_context_id="my_domain",
    current_evidence=["test_results"],
)
state = engine.build_active_state(binding, current_state="start")
outcome = engine.step(state, transition_id="start_to_reviewed")
# outcome.kind → OutcomeKind.CONTINUE (if evidence and gate pass)
# outcome.llm_prompt_state → the JSON for the model to read
```

## What this is NOT

- Not a prompt template or system prompt
- Not a retrieval/RAG system for FPF text
- Not a replacement for the full FPF spec
- Not a symbolic AI / expert system (the LLM interprets; logic + guards constrain)
- Not a framework to build on top of — it is a small self-contained package
- Not a panacea for agent drift; it reduces and explains drift, but it does not eliminate it

## Known design decisions

- `satisfied: true` on a vacuously true implication (antecedent false → implication holds trivially) is mathematically correct. The action is suppressed on HINT/WARN rules, so the model sees no misleading instruction. The `satisfied` flag itself stays honest.
- `demo_walk()` auto-fires the first available transition. It is for testing and examples only, not for operational use. In real use, the LLM calls `step()` and `attempt_transition()` with explicit choices.
- Publications are registered on the map but stay out of the step/guard/logic path. They are for publish-type moves only.

prichindel.com | 2026-07-10 | v1.4.25
