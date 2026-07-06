# prichindel.com Agentic Thinking Map

**v1.3.0** — [FPF (First Principles Framework)](https://github.com/ailev/FPF) compiled into a semi-formal thinking map for agentic AI guidance.

A Python package that gives an AI model a small, structured board to reason on — one move at a time. Instead of freeform text generation, the model navigates a pre-shaped semantic field with deterministic guards and propositional logic constraints.

**[Visual architecture →](ARCHITECTURE.md)** — module graph, step flowchart, floor map, evidence lifecycle, slice structure, deploy sequence diagram.

## What it does

You define a domain as a semantic map (contexts, roles, gates, evidence, transitions). The model gets a per-move slice — just the current transition, its gate, its evidence, and whether it can fire. Deterministic guards enforce hard constraints the model cannot override. Propositional logic rules (NOT, AND, OR, XOR, IMPLIES, IFF) provide decision glue between the semantic primitives and the model's reasoning.

The model's job is not "what does FPF mean?" — it is: **given this semantic map and this state, what is the best lawful next move?**

## Quick start

```bash
# No dependencies. Python 3.12+.

# Verify the package (21 checks)
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
├── verify.py                 Self-verification harness (21/21 checks)
├── examples.py               5 deploy decision scenarios (missing evidence, role conflict, logic glue, truth table)
├── README.md                 Full documentation (any-model readable)
├── SOURCES.md                Source attribution (FPF spec + Mitev lectures)
├── FPF_SOURCE_TO_CODE_RELATION_AUDIT.md   50-item relation audit
├── FPF_AUDIT_RESPONSE.md     Audit response with design decisions
├── WHY_THIS_EXISTS.md            Compiled FPF vs raw FPF — the triple tax problem
├── FPF_FLOOR_MAP.md              Semantic floor map (5 floors, TTL derivation)
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

## Design principles

- **Only add structure when it changes agentic behavior** — not for source fidelity alone
- **Per-step chew = one move slice** — never context feast
- **Horizontal operational clarity** over vertical semantic completeness
- **Compile-time richness** over runtime payload growth

## Using as a dependency

This package is the reasoning engine. Your domain maps run on top of it.

```bash
pip install git+https://github.com/igareosh/prichindel.com-agentic-thinking-map.git
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

## License

MIT. See [LICENSE](LICENSE).

---

**prichindel.com** — v1.2.1 — 2026-06-26
