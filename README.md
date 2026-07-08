# prichindel.com Agentic Thinking Map

**v1.4.3** — [FPF (First Principles Framework)](https://github.com/ailev/FPF), compiled into a small traversal map for LLM agents.

A Python package that gives a model a bounded move board instead of a giant framework to digest at runtime. Instead of rereading a sprawling semantic corpus and improvising from it, the model gets a small JSON slice: what context it is in, what move is open, what evidence is missing, what is risky, and what outcome class applies.

**[Visual architecture →](ARCHITECTURE.md)** — module graph, step flowchart, floor map, evidence lifecycle, slice structure, deploy sequence diagram.

## Why this exists

FPF is valuable, but it is large, clumsy at runtime, and poorly shaped for direct model consumption. A human can read a 51k-line framework, understand its distinctions, and apply them carefully. A model usually does something else: it absorbs the vocabulary, performs the tone of the framework, and still drifts on the actual task.

This package exists because the useful part is not making the model sound more scientific. The useful part is compiling the parts of FPF that help operational decisions into something small, explicit, and inspectable. We took what mattered for bounded traversal, left out what would bloat or bias the model, and evolved the result as publishers of a practical library rather than trying to reproduce the whole upstream framework inside another AI mega-system.

The goal is simple: give the model enough structure to behave understandably, without building a cage so elaborate that it becomes another source of drift.

We do not compete with FPF and we do not need to. FPF stays FPF: broad, ambitious, and useful as a frame. This library is the smaller usable tool for people who want the frame without carrying the whole corpus into every project.

## What it does

You define a domain as a semantic map: contexts, roles, gates, evidence, transitions. The model gets a per-move slice, not a theory dump. Deterministic guards handle the hard checks. Propositional logic rules (NOT, AND, OR, XOR, IMPLIES, IFF) provide explicit decision glue between the semantic primitives and the current state.

The model's job is not "what does FPF mean?" It is: **given this map and this state, what is the best lawful next move?**

In practice this does two useful things:

- it reduces unexplained drift by moving state tracking and hard checks out of freeform model reasoning
- it gives the model simple, understandable outcomes such as `CONTINUE`, `COLLECT_EVIDENCE`, `BRIDGE`, `IDLE`, `ESCALATE`, instead of making it reconstruct its own epistemic condition from scratch

This is not a panacea. Models still miss information. They still drift. But with a bounded traversal map, the failure mode becomes much easier to explain: missing evidence, wrong context, blocked move, stale basis, unlicensed bridge. The weirdness gets smaller because the state is smaller.

## Provable practical gains

The improvements here are intentionally simple and operational:

- less random drift, because the agent reads explicit state instead of reconstructing state from prose
- fewer unlawful moves, because guards and scoped transitions check them before the model improvises
- clearer failure, because "why blocked" is surfaced directly
- smaller runtime payload, because the model gets a slice, not a corpus
- easier debugging, because outcomes are discrete and inspectable

That is the whole point: practical gain, not intellectual theater.

## Quick start

```bash
# No dependencies. Python 3.12+.

# Verify the package (22 checks)
python -m fpf_thinking_map.verify

# Run the deploy decision scenario
python -m fpf_thinking_map.examples
```

## Package contents

```
fpf_thinking_map/
├── primitives.py             10 semantic objects from FPF spec
├── state.py                  SemanticMap + RuntimeBinding + ActiveState + slice()
├── guards.py                 9 deterministic guards (context, role, gate, evidence, assignment, speech act, readiness)
├── logic.py                  6 logic operators + decision rules + LogicLayer
├── traversal.py              Step engine with 10 lawful outcomes (incl. IDLE, BRIDGE)
├── verify.py                 Self-verification harness (22/22 checks)
├── examples.py               5 deploy decision scenarios (missing evidence, role conflict, logic glue, truth table)
├── README.md                 Full documentation (any-model readable)
├── SOURCES.md                Source attribution (FPF spec + Mitev lectures)
├── FPF_SOURCE_TO_CODE_RELATION_AUDIT.md   50-item relation audit
├── ADVISORIES.md             Publisher advisories for integrators — not defects, deliberate minimalism + how to tighten it
├── FPF_AUDIT_RESPONSE.md     Audit response with design decisions
├── WHY_THIS_EXISTS.md            Compiled FPF vs raw FPF — the triple tax problem
├── FPF_FLOOR_MAP.md              Semantic floor map (5 floors, TTL derivation)
├── REJECTED_C32_CANDIDATE_SYNTHESIS.md    C.32 rejection (activation bias)
└── REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md NQD/OEE rejection (bias injector)
```

## dev_mcp — testing surface (GitHub only, not on PyPI)

`verify.py` proves the engine's own logic is internally consistent. It doesn't prove the compiled map covers the breadth of the original FPF spec — `examples.py` has one domain, five scenarios. `dev_mcp/` is an MCP server for constructing scenarios ad hoc and driving them against the documents that already ground FPF semantics in this repo: `SOURCES.md` (which spec section each primitive is supposed to enforce), `FPF_SOURCE_TO_CODE_RELATION_AUDIT.md` (a cited 50-item gap backlog), and `ADVISORIES.md` (deliberate-minimalism findings for integrators — not defects, but real defaults you should know about before assuming they match your domain).

Not shipped in the package — `pyproject.toml` only builds `fpf_thinking_map*`, so this stays a repo-only dev tool by construction, for whoever's interested enough to dig past `pip install`. `run_scenario` requires a `scope`: `"core"` for testing this library's own shipped primitives (our responsibility, our tracking), `"user-extension"` for testing a domain map built on top (your responsibility, your repo). Full docs, install steps, self-test, worked example: [dev_mcp/README.md](dev_mcp/README.md).

## Relationship to ailev/FPF

This package is built on [ailev/FPF](https://github.com/ailev/FPF) by Anatoly Levenchuk. It is an independent implementation — our own research and code, MIT-licensed, with further development rights.

It is not an attempt to "finish" FPF, replace FPF, or repackage the whole corpus for LLM ingestion. It is a selective compilation for agentic traversal.

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

## Scope and non-goals

This library is intentionally small in scope.

- It is for bounded, stepwise agent traversal in a defined domain.
- It is for making model behavior more understandable, not more magical.
- It is for simple +/- operational decisions in context, not for open-ended idea generation.
- It is for constraining and instrumenting an agent run, not replacing the model.

It is not:

- a full semantic ingestion layer for all of FPF
- a universal reasoning engine
- a replacement for ordinary application logic or policy code
- a proof that an LLM will behave correctly just because the map exists
- Memory-Augmented Generation (MAG) — no embeddings, no vector store, no cross-session retrieval, ever, inside this engine. Rejected deliberately and permanently, not by omission. See below.

## What this actually guarantees

fpf does not ship better reasoning. It ships **inspectability**: did the agent follow the lawful path, and was evidence honestly reported at the one place that matters — the wire between what the agent actually did and what this library was told.

Take the stagnation counter as the concrete case. It bounds repetition — but only if the integration maps one real attempt to one `step()` call, and only adds evidence when something genuinely new was found. Whether that actually catches a real LLM thrashing depends entirely on whether the calling harness wires evidence honestly, not just "a tool returned something." That wiring discipline lives outside this library, in whatever integrates it — an agent loop, an MCP server, application code. fpf can't verify that discipline was followed; it can only guarantee that if it was, repetition is bounded.

That boundary is the correct seam, not a gap to apologize for. Judging whether a piece of evidence is actually meaningful is a semantic question, and semantic questions need prompting, an LLM judge, or domain logic to answer — which is exactly where that belongs: outside fpf, at the evidence-wiring layer, not folded into a library whose entire value is staying small and deterministic. If you want semantics and clever prompting, that's the plug-in point.

**This is also why Memory-Augmented Generation (MAG) is rejected as fpf's own architecture, deliberately and permanently.** MAG — retrieval, embeddings, cross-session recall — solves a different problem (what did we discuss three sessions ago) than fpf solves (is this move lawful right now), and it needs exactly the dependency profile this library rules out by design. That is a scope boundary, not a verdict on MAG as a technique: a MAG system is a legitimate thing to run *upstream* of fpf. Whatever it retrieves becomes an evidence_id in `RuntimeBinding.current_evidence` like any other — fpf doesn't care how evidence was produced, only whether it's present, fresh, and licensed. Memory belongs at the evidence-wiring layer, alongside every other semantic judgment this library deliberately doesn't make.

## Sources

- **[FPF (First Principles Framework)](https://github.com/ailev/FPF)** by Anatoly Levenchuk — transdisciplinary specification (~51k lines). We extracted 10 semantic primitives and 9 guard rules. This is a compiled distillation, not a port.
- **Computational logic (Mitev L.)** — "Bazele programarii logice." 6 propositional logic operators and the Wumpus World agent navigation pattern.

Full attribution in [SOURCES.md](fpf_thinking_map/SOURCES.md).

## Why it works

The core advantage is not "more theory." It is less runtime burden.

Without a compiled map, the model keeps re-addressing its own run: am I allowed to move, did I already satisfy the gate, am I missing evidence, am I in the wrong context, am I done or blocked? That self-management loop is where a lot of bad agent behavior comes from.

This package turns that loop into a small stateful instrument panel. The model sees what can fire, what cannot, and why. That is enough of an operating surface for many practical agent tasks. Not a panacea, not a grand theory of intelligence, just enough window and file-handles for the model to open the right thing without smashing the house.

The bottleneck was never raw model capability — it's self-management overhead eating the capability that's already there. Most orgs running these models, at any scale, hit that ceiling: infra and process that never actually asked the model for full capacity, so upgrading the model changes nothing. This library doesn't make the model smarter. It shrinks what the model has to hold in its head at any one step, so whatever capability is actually there gets spent on the real problem instead of on self-management overhead.

Clean product truth:

- FPF is the frame.
- This library is the usable tool.
- It keeps the frame where it helps, removes the bloat where it hurts, and gives agents a small operational board that produces simpler, more provable behavior.

## Why v1.1 exists — reasoning about reasoning is the bug

When an LLM navigates a multi-step decision, it faces the same sub-questions at every step: "Is my evidence still valid? Am I going in circles? Is there another path? Why am I blocked?" Without structure, the model re-derives these answers from scratch each time — re-reasoning on its own prior reasoning. Each pass costs tokens, drifts from the original question, and eventually the context fills up with the model arguing with itself about whether it already checked something it checked three steps ago.

This is not a hypothetical failure mode. It is the default behavior of every frontier model on multi-step tasks. The model loops, the reasoning amplifies, the token budget runs out, and the final output is whatever the model managed to squeeze out before the window closed. The answer is technically "an answer" in the same way that a student who ran out of exam time scribbles something in the last 30 seconds.

**v1.1 replaces re-reasoning with arithmetic.** Instead of asking the model "is this evidence still good?" on every step, the code counts hops and computes freshness from a trust formula. Instead of asking "am I stuck or done?", the engine checks transitions, bridges, and actions — and returns a discrete outcome (IDLE, BRIDGE, COLLECT_EVIDENCE). Instead of hiding "why can't I proceed?" behind a boolean, the slice spells out the blockers in plain text.

The model's job shrinks from "figure out the entire epistemic state of your own reasoning" to "read this small JSON, pick the next move." The thinking map handles what the model is bad at (tracking state across steps) and leaves it what it is good at (interpreting context and choosing between options).

## v1.2.1 changes

- **TTL evidence decay** — evidence degrades CURRENT → STALE → EXPIRED as traversal steps accumulate. The rate is computed from the FGR trust tuple: formal evidence from reliable sources lasts longer, anecdotal evidence expires fast. No more static evidence that stays green forever across a 10-step traversal. See [FPF_FLOOR_MAP.md](fpf_thinking_map/FPF_FLOOR_MAP.md) for the 5-floor vertical map.
- **EvidenceFresh proposition** — `EvidenceFresh("test_results")` returns False when evidence has TTL-decayed. The deploy readiness rule now uses this instead of raw presence checks. The logic layer uses math, not re-reasoning, to decide if evidence is still valid.
- **IDLE outcome** — distinguishes "at rest, nothing actionable" from "stuck, need input." When the map is done, it says so — the model does not loop trying to find work that does not exist.
- **Bridge traversal** — when dead-ended in a context, the engine checks precomputed bridge targets. If a bridge leads to a context with transitions, the agent gets a concrete cross-context escape with target info, entry states, and translation loss. No more dead ends that the model tries to reason its way out of.
- **Slice blockers** — `slice()` now explains *why* a move cannot fire: which gate abstained, which evidence is missing, which guard denied. The operator sees the problem, not just a red light.
- **Evidence status in prompt** — the LLM prompt state now includes per-evidence freshness and TTL remaining. The model sees "test_results: 3 steps left" instead of just "test_results: exists." Decisions informed by countdown, not by guessing.
- **Response contract** — every slice now ends with a `response_contract`: the structured template the model must fill when responding. Pre-filled fields (scope, basis with freshness/TTL, allowed use, not allowed use, modality, canonical terms, audience) come from the computed state. Empty fields (claim, risky aliases) are for the model. This is why all the code exists — so the contract has precomputed, validated values instead of being re-derived by the model from scratch.

## v1.3.0 changes

- **Bridge crossing is enforced, not just advertised** — `ActiveState.cross_bridge()` / `ThinkingMapTraversal.attempt_bridge()` actually perform a cross-context hop and check `substitution_license` against `risk_level` before mutating state. An unlicensed bridge under `high`/`critical` risk is refused (`ESCALATE`), not silently allowed. Before this, `bridge_options()` was advisory metadata only — the model decided for itself whether a lossy translation was acceptable.
- **`include_full_state=False`** — `step()` can now ship the scoped `slice()` alone, without the whole board bolted on. Default stays `True`; opt in when the caller already knows its `transition_id` and wants the lean payload.
- 21/21 self-verification checks (`python -m fpf_thinking_map.verify`), two new: bridge crossing and lean-slice payload shape.

## v1.4.0 changes

- **Stagnation counter** — `ActiveState.register_visit()` / `visit_count` / `visits_remaining` / `is_stagnant` count consecutive `step()`s at the same `(context, state)` pair with no new evidence gathered; the counter resets the moment the evidence set changes. `visits_remaining` mirrors `ttl_remaining`'s exact shape — a countdown, not a boolean. Surfaced in both `slice()` and `to_llm_prompt_state()` as a `stagnation` block. Pure signal: no new outcome kind, nothing blocks, no restraint added to the model's options. Closes a real blind spot — `MoveTrace` is deliberately last-move-only (no narrative accumulation), so the engine previously had no way to notice "I've revisited this exact state N times with nothing new to show for it."
- The guarantee is conditional, and the docs say so plainly: this tracks evidence *set membership*, not evidence *meaning*. It bounds repetition only if the integration maps one real attempt to one `step()` call and only adds evidence that's genuinely new — see [What this actually guarantees](#what-this-actually-guarantees).
- 22/22 self-verification checks, one new: `check_stagnation_counter`.

## v1.4.1 changes

- **`ADVISORIES.md`** — publisher advisories for integrators, ships in the package alongside `SOURCES.md` and the audit backlog. Not defects: places the library deliberately stays minimal and leaves a real decision to whoever builds a domain map on top of it, with what the default is, why, and exactly how to tighten it. v1 ships two, both found by actually running scenarios through `dev_mcp` rather than by inspection: evidence staleness warns but doesn't block by default (ADV-01), `risk_level` doesn't filter `possible_transitions` on its own (ADV-02).
- `dev_mcp` gains `get_advisories()`, same read-the-doc pattern as `get_fpf_source_mapping`/`get_audit_gaps`.
- 13/13 `dev_mcp` self-test checks (one new).

## v1.4.2 changes

- **Four more advisories** (`ADV-03`–`ADV-06`), found the same way as `ADV-01`/`ADV-02` — running scenarios through `dev_mcp`, not inspection. The one to actually read: **`ADV-03`** — `RuntimeBinding.active_context_id` is self-asserted input, never verified against having actually crossed a bridge; a caller can claim any context directly and get the identical `CONTINUE` a licensed `cross_bridge()` call would produce. `ADV-04` — contradiction detection between `DecisionRule`s is opt-in via `exclusive_with`, not inferred from opposite-looking action names. `ADV-05` — gate `DEGRADE` only distinguishes partial evidence when related facts are grouped into *one* `GateCheck`; split across separate checks, "one of three known" collapses to indistinguishable from "none known." `ADV-06` — `agency_level` (PASSIVE/REACTIVE/AUTONOMOUS/DELIBERATIVE) is descriptive metadata only, same shape as `risk_level` (`ADV-02`) — nothing stops a `PASSIVE` role from firing what a `DELIBERATIVE` role can.
- `check_advisories_content` now asserts all six advisory IDs are present, not just the original two.

## v1.4.3 changes

- **`ADV-07`** — the sharpest advisory yet, called out at the top of `ADVISORIES.md` alongside `ADV-03`. `RiskAbove(threshold)` matches `risk_level` against a fixed table via plain dict lookup; anything not found — including a correctly-spelled value in the wrong case (`"CRITICAL"` vs. `"critical"`) — silently resolves to `"normal"`. Confirmed directly: a `RiskAbove("critical")` rule wired exactly as `ADV-02` recommends returns the *opposite* routed action for `"CRITICAL"` vs. `"critical"`, with no error, no warning, `consistency_check()` reporting `True` either way. Following the library's own documented fix for `ADV-02` does not protect you from this — normalize and validate `risk_level` at your harness boundary before it reaches the engine.
- `check_advisories_content` now asserts all seven advisory IDs.

## Design principles

- **Only add structure when it changes agentic behavior** — not for source fidelity alone
- **Per-step chew = one move slice** — never context feast
- **Horizontal operational clarity** over vertical semantic completeness
- **Compile-time richness** over runtime payload growth

## Using as a dependency

This package is the compiled map, not a thinking replacement for the model. Denying unlawful moves is only half the job. The bigger half is returning the lawful surface as a small, plain-JSON slice: what can fire, what is missing, what is risky, why a move is blocked, what response shape is expected. That lets the model self-address its own run with simple signals such as `can_fire`, `blockers`, and `outcome.kind` instead of re-reasoning about its state from prose.

```bash
pip install fpf-thinking-map
```

```python
from fpf_thinking_map import (
    SemanticMap, ContextPrimitive, RolePrimitive, TransitionPrimitive,
    GatePrimitive, GateCheck, EvidencePrimitive, CommitmentPrimitive,
    FGR, Freshness, SemanticFloor, DeonticModality, AgencyLevel,
    RuntimeBinding, ThinkingMapTraversal,
    LogicLayer, DecisionRule, RuleKind, EvidenceFresh,
)

# 1. Build your domain map
sm = SemanticMap()
sm.register_context(ContextPrimitive("sales", "Sales Process",
    glossary={"lead": "potential customer", "deal": "qualified opportunity"},
    invariants=["no invoice without signed contract"],
))
sm.register_role(RolePrimitive("sales_rep", "Sales Rep", "sales",
    incompatible_with=["approver"],
))
sm.register_gate(GatePrimitive("deal_gate", "Deal Gate", "sales", checks=[
    GateCheck("contract", "Signed contract", required_evidence=["signed_contract"]),
]))
sm.register_transition(TransitionPrimitive(
    "qualify", "Qualify Lead", "sales", "new_lead", "qualified",
    required_evidence=["contact_info"],
))

# 2. Build your logic rules (optional)
logic = LogicLayer()
logic.add_rule(DecisionRule(
    name="deal_ready",
    condition=EvidenceFresh("signed_contract"),
    action_if_true="proceed", action_if_false="collect_signature",
    kind=RuleKind.ROUTE, tags=["sales"],
))

# 3. Create engine and step
engine = ThinkingMapTraversal(sm, logic_layer=logic)
state = engine.build_active_state(
    RuntimeBinding(task="qualify lead", actor_role_ids=["sales_rep"],
                   active_context_id="sales", current_evidence=["contact_info"]),
    current_state="new_lead",
)
outcome = engine.step(state)
# outcome.kind → CONTINUE, COLLECT_EVIDENCE, IDLE, BRIDGE, ...
# outcome.llm_prompt_state → JSON for the model (includes response_contract)
```

The engine has no domain-specific code. The deploy example in `examples.py` is a reference implementation — your domain maps import the engine and build their own SemanticMaps, gates, and rules.

## Compatibility

Built with Claude Code (Anthropic claude-sonnet-4-6). Tested and verified to work with:

| Model family | Status | Notes |
|-------------|--------|-------|
| **Anthropic Claude** (Sonnet, Opus, Haiku) | Works | Built and tested here. Slice size fits comfortably in context. |
| **OpenAI GPT** (GPT-4o, o1, o3) | Works | Used for the 50-item source-to-code relation audit. Reads the primitives, logic rules, and prompt state correctly. |
| **Any model that reads JSON and follows structured constraints** | Should work | The package outputs plain dicts. No model-specific prompting. |

This is not a compliance seal. It means: we used these models against this package and they produced correct, usable results. The per-move slice is small enough for mid-tier models. The logic and guard outputs are plain JSON — no special tokenization or prompt format required.

## Why release this

We release this because it is useful beyond our own stack.

- It captures a practical subset of FPF in a form models can actually use.
- It gives agent builders a small constraint surface instead of another giant AI framework.
- It helps turn model failure from mystical drift into inspectable state.
- It stays intentionally narrow, so it can remain legible instead of becoming another overbuilt "agent platform."

## Credits

- **igareosh** — project direction, scope discipline, practical use-case pressure, and product truth
- **Claude Code (Anthropic)** — implementation support, library iteration, and earlier release preparation
- **Codex / OpenAI** — product framing polish, packaging cleanup, verification, and release-readiness work

## License

MIT. See [LICENSE](LICENSE).

---

**prichindel.com** — v1.4.3 — 2026-07-08
