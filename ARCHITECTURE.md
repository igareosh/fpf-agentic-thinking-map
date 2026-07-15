# Architecture

Visual scheme of the thinking map — what each part does and how they fit together.

## Module dependency

```mermaid
graph LR
    P[primitives.py<br/>12 primitives + 5 floors]
    S[state.py<br/>binding + active state + slice]
    G[guards.py<br/>9 hard constraints]
    L[logic.py<br/>6 operators + rules]
    T[traversal.py<br/>step engine + 10 declared outcomes]
    E[examples.py<br/>5 scenarios]
    V[verify.py<br/>22 checks]

    P --> S
    P --> G
    P --> L
    S --> G
    S --> L
    S --> T
    G --> T
    L --> T
    T --> E
    S --> E
    P --> E
    T --> V
    S --> V
    G --> V
    L --> V
    E --> V

    style P fill:#2d5016,color:#fff
    style S fill:#1a3a5c,color:#fff
    style G fill:#5c1a1a,color:#fff
    style L fill:#4a3728,color:#fff
    style T fill:#1a4a4a,color:#fff
    style E fill:#3a3a3a,color:#fff
    style V fill:#3a3a3a,color:#fff
```

## How a step works

`step()` is the normal runtime path. It can return 6 of the 10 declared outcomes. `ESCALATE` only comes from `attempt_bridge()` (below). `ASK`, `PUBLISH`, and `REVISE_PLAN` exist in `OutcomeKind`, but nothing returns them yet.

```mermaid
flowchart TD
    START([step called]) --> INC[step_count++<br/>drives TTL decay]
    INC --> CTX{active<br/>context?}
    CTX -->|no| CF[CHANGE_FRAME]
    CTX -->|yes| XCTX{focused mode:<br/>transition in<br/>active context?}
    XCTX -->|no, mismatch| ABSTAIN[ABSTAIN]
    XCTX -->|yes| LOGIC["evaluate logic rules<br/>(6-operator composition,<br/>see next section)"]
    LOGIC --> CONSIST{consistent?}
    CONSIST -->|contradiction| ABSTAIN
    CONSIST -->|ok| GUARDS[run 9 guards]
    GUARDS --> GPASS{all<br/>allow?}
    GPASS -->|deny + evidence path| CE1[COLLECT_EVIDENCE]
    GPASS -->|deny + no path| ABSTAIN
    GPASS -->|allow| EVCHECK{evidence<br/>gaps?}
    EVCHECK -->|gaps| CE2[COLLECT_EVIDENCE]
    EVCHECK -->|complete| TRANS{transitions<br/>available?}
    TRANS -->|yes| CONTINUE[CONTINUE<br/>+ slice + contract]
    TRANS -->|no + actions| CONTINUE2[CONTINUE]
    TRANS -->|no + bridges| BRIDGE[BRIDGE<br/>+ target contexts, advisory only]
    TRANS -->|nothing| IDLE[IDLE<br/>at rest]

    style CF fill:#8b6914,color:#fff
    style ABSTAIN fill:#8b1a1a,color:#fff
    style CE1 fill:#4a3728,color:#fff
    style CE2 fill:#4a3728,color:#fff
    style CONTINUE fill:#2d5016,color:#fff
    style CONTINUE2 fill:#2d5016,color:#fff
    style BRIDGE fill:#1a3a5c,color:#fff
    style IDLE fill:#3a3a3a,color:#fff
```

`step()` does not cross a bridge by itself. It only reports that a bridge is available (`BRIDGE`). Actually crossing it is a separate call:

```mermaid
flowchart LR
    BR([attempt_bridge<br/>called]) --> LIC{fidelity contract:<br/>substitution_license<br/>vs. risk_level}
    LIC -->|unlicensed +<br/>high/critical risk| ESC[ESCALATE]
    LIC -->|refused, other reason| AB2[ABSTAIN]
    LIC -->|licensed| CROSS[cross_bridge<br/>state mutates]
    CROSS --> CONT3[CONTINUE]

    style ESC fill:#8b6914,color:#fff
    style AB2 fill:#8b1a1a,color:#fff
    style CONT3 fill:#2d5016,color:#fff
```

`attempt_transition()` is simpler than `step()`. It either:

- returns `ABSTAIN` if the move is invalid
- returns `COLLECT_EVIDENCE` if required evidence is missing
- returns `CONTINUE` if the transition succeeds

## Logic layer — how the 6 operators compose

These are real shipped rules from `examples.build_deploy_rules()`, not toy examples. A rule is usually made from several small facts combined through logic operators.

```mermaid
graph TB
    subgraph ATOMS["Atomic props — facts read off ActiveState"]
        ETF["EvidenceFresh<br/>test_results"]
        EAF["EvidenceFresh<br/>owner_approval"]
        EA["EvidencePresent<br/>owner_approval"]
        ET["EvidencePresent<br/>test_results"]
        GD["GatePasses<br/>deploy_gate"]
        GB["GateBlocked<br/>deploy_gate"]
        HG["HasMissingEvidence"]
        RA["RoleActive<br/>analyst"]
        RP["RoleActive<br/>approver"]
        ER["EvidencePresent<br/>rollback_plan"]
        TD["TransitionAvailable<br/>ready_to_deploy"]
        RDY["InState<br/>ready_for_decision"]
        HR["RiskAbove<br/>high"]
    end

    ETF --> A1{AND}
    EAF --> A1
    A1 --> A2{AND}
    GD --> A2
    A2 --> R1["deploy_readiness — ROUTE<br/>proceed_to_deploy / not_ready<br/>excludes: block_transition"]

    GB --> I1{IMPLIES}
    HG --> I1
    I1 --> R2["gate_blocked_implies_collect — HINT<br/>collect_evidence"]

    EA --> N1{NOT}
    N1 --> R3["evidence_gap_detected — WARN<br/>request_approval"]

    ET --> A3{AND}
    ETF --> N2{NOT}
    N2 --> A3
    A3 --> R4["evidence_decay_warning — WARN<br/>evidence_stale_refresh_needed"]

    RA --> X1{XOR}
    RP --> X1
    X1 --> R5["role_separation — BLOCK<br/>valid_role_assignment / role_conflict"]

    ER --> O1{OR}
    TD --> N3{NOT}
    N3 --> O1
    O1 --> R6["recovery_path_exists — WARN<br/>safe_to_proceed / no_safety_net"]

    RDY --> F1{IFF}
    GD --> F1
    F1 --> R7["readiness_equivalence — HINT<br/>state_gate_aligned / state_gate_mismatch"]

    HR --> A4{AND}
    HG --> A4
    A4 --> I2{IMPLIES}
    I2 --> R8["risk_escalation — ROUTE, risk-sensitive<br/>escalate_if_risky"]

    R1 --> LAYER["LogicLayer.evaluate_for(tags)"]
    R2 --> LAYER
    R3 --> LAYER
    R4 --> LAYER
    R5 --> LAYER
    R6 --> LAYER
    R7 --> LAYER
    R8 --> LAYER

    LAYER --> FACTS["facts<br/>HINT + WARN rules"]
    LAYER --> ACTIONS["actions<br/>ROUTE + BLOCK rules"]
    ACTIONS --> CONS["consistency_check()<br/>exclusive_with contradictions"]

    CONS -->|contradiction found| AB4["step(): ABSTAIN"]
    CONS -->|consistent| PROCEED["step(): proceed to guards"]

    style ATOMS fill:#0d1117,color:#fff
    style R1 fill:#1a4a4a,color:#fff
    style R2 fill:#4a3728,color:#fff
    style R3 fill:#4a3728,color:#fff
    style R4 fill:#4a3728,color:#fff
    style R5 fill:#5c1a1a,color:#fff
    style R6 fill:#4a3728,color:#fff
    style R7 fill:#4a3728,color:#fff
    style R8 fill:#1a4a4a,color:#fff
    style LAYER fill:#1a3a5c,color:#fff
    style AB4 fill:#8b1a1a,color:#fff
    style PROCEED fill:#2d5016,color:#fff
```

All 6 operators are used in real rules. The main point is simple: the engine does not read one flag and jump. It combines several facts first, then decides.

Two rule kinds never participate in contradiction checking: `HINT` and `WARN`. They are informational only. Only `ROUTE` and `BLOCK` produce actions, and only those actions are checked for conflicts. If two action rules clash, `step()` stops and returns `ABSTAIN` before guards run.

## Semantic floors and TTL decay

```mermaid
graph TB
    subgraph "Floor 0 — STRUCTURAL"
        F0[ContextPrimitive<br/>ContextBridge<br/>RolePrimitive<br/>TransitionPrimitive<br/>GatePrimitive def]
        F0TTL["TTL: ∞<br/>never expires"]
    end

    subgraph "Floor 1 — BINDING"
        F1[RoleAssignment<br/>CommitmentPrimitive<br/>WorkPlanPrimitive]
        F1TTL["TTL: 10 steps"]
    end

    subgraph "Floor 2 — EVIDENTIARY"
        F2[EvidencePrimitive<br/>FGR trust tuple]
        F2TTL["TTL: max 1, round F×R×8<br/>F=0.8 R=0.9 → 6 steps<br/>F=0.2 R=0.3 → 1 step"]
    end

    subgraph "Floor 3 — OPERATIONAL"
        F3[SpeechActPrimitive<br/>WorkPrimitive<br/>GatePrimitive eval]
        F3TTL["TTL: 2 steps"]
    end

    subgraph "Floor 4 — PUBLICATION"
        F4[PublicationPrimitive]
        F4TTL["TTL: inherited<br/>from source"]
    end

    F0 ~~~ F1 ~~~ F2 ~~~ F3 ~~~ F4

    style F0 fill:#2d5016,color:#fff
    style F0TTL fill:#2d5016,color:#fff
    style F1 fill:#1a3a5c,color:#fff
    style F1TTL fill:#1a3a5c,color:#fff
    style F2 fill:#4a3728,color:#fff
    style F2TTL fill:#4a3728,color:#fff
    style F3 fill:#5c1a1a,color:#fff
    style F3TTL fill:#5c1a1a,color:#fff
    style F4 fill:#3a3a3a,color:#fff
    style F4TTL fill:#3a3a3a,color:#fff
```

## Evidence lifecycle

```mermaid
stateDiagram-v2
    [*] --> CURRENT: evidence added<br/>at step N
    CURRENT --> CURRENT: age < TTL
    CURRENT --> STALE: age ≥ TTL<br/>guard warns
    STALE --> STALE: age < 2×TTL
    STALE --> EXPIRED: age ≥ 2×TTL<br/>evidence dead
    EXPIRED --> [*]

    CURRENT --> CURRENT: EvidenceFresh ✓
    STALE --> STALE: EvidenceFresh ✗
    EXPIRED --> EXPIRED: EvidenceFresh ✗
```

## The slice — what the model reads per move

```mermaid
graph TD
    subgraph SLICE["slice(transition_id)"]
        MOVE["move<br/>id, label, from → to"]
        GATE["gate<br/>decision: pass/insufficient/partial/block<br/>missing evidence"]
        EV["evidence<br/>available: [{id, freshness, ttl_remaining}]<br/>missing: [ids]"]
        ROLES["roles<br/>[{id, label}]"]
        FIRE["can_fire: true/false"]
        BLOCK["blockers<br/>[why it can't fire]"]
        RC["response_contract<br/>claim, scope, basis,<br/>allowed_use, not_allowed_use,<br/>obligations, audience,<br/>correct_terms, risky_aliases"]
    end

    MOVE --> GATE --> EV --> ROLES --> FIRE --> BLOCK --> RC

    MODEL([model reads slice<br/>fills claim + risky_aliases<br/>picks next move])
    RC --> MODEL

    style SLICE fill:#0d1117,color:#fff
    style RC fill:#2d5016,color:#fff
    style MODEL fill:#1a3a5c,color:#fff
```

`gate.decision` uses the JSON value, not the Python enum name. So the model sees `"insufficient"` or `"partial"`, not `GateDecision.ABSTAIN` or `GateDecision.DEGRADE`.

## The triple tax — raw FPF vs compiled

```mermaid
graph LR
    subgraph RAW["Raw FPF (51k lines)"]
        direction TB
        R1[Pass 1: Parse<br/>holon? episteme? ontic?]
        R2[Pass 2: Aggregate<br/>FPF vocabulary → task vocabulary]
        R3[Pass 3: Generate<br/>FPF-flavored prose output]
        R1 --> R2 --> R3
    end

    subgraph COMPILED["Compiled thinking map"]
        direction TB
        C1["Read JSON slice<br/>{can_fire: false, blockers: [...]}"]
        C2["Fill response contract<br/>{claim: '...', risky_aliases: [...]}"]
        C1 --> C2
    end

    RAW -->|"3 passes<br/>N × concept layers<br/>re-reasoning"| OUT1[FPF-flavored prose]
    COMPILED -->|"1 pass<br/>fill-in-the-blank<br/>precomputed"| OUT2[Structured decision]

    style RAW fill:#5c1a1a,color:#fff
    style COMPILED fill:#2d5016,color:#fff
    style OUT1 fill:#5c1a1a,color:#fff
    style OUT2 fill:#2d5016,color:#fff
```

Plain version: the compiled map is much smaller and cheaper to run than raw FPF in-context. That part is measured. The exact inner "pass-by-pass" story in the diagram is explanatory, not something we claim to have fully measured step by step.

[`TRIPLE_TAX_CALCULUS.md`](docs/deep/TRIPLE_TAX_CALCULUS.md) measures the token/cost side directly: on 5 shipped decision points, the compiled slice was 4668.8x smaller than the full raw spec token load of 2,247,567 tokens.

Important limit: the raw 3-pass path in the diagram was **not** live-tested end to end, because the raw spec is too large for any practical context window. Only token size was measured there. On the compiled side, live runs were measured, but not as a stable literal cognition trace. So the strong claim here is the runtime size/cost difference, not a precise psychological model of how the LLM "thinks."

## Deploy scenario — full flow

```mermaid
sequenceDiagram
    participant B as RuntimeBinding
    participant S as ActiveState
    participant G as GuardEngine
    participant L as LogicLayer
    participant T as ThinkingMapTraversal
    participant M as Model

    B->>S: bind(task, actor, evidence, context)
    Note over S: step_count = 0<br/>evidence timestamped

    loop each step
        T->>S: step_count++
        T->>S: check context, transitions
        T->>L: evaluate logic rules
        L-->>T: facts + actions + consistency
        T->>G: run 9 guards
        G-->>T: allow/deny/warn per guard
        T->>S: build slice(transition_id)
        S-->>T: {move, gate, evidence, blockers, response_contract}
        T-->>M: Outcome + slice JSON
        Note over M: reads slice<br/>fills contract<br/>picks next move
        M->>T: attempt_transition(chosen_id)
        T->>S: transition_to(id)
        Note over S: state changes<br/>evidence ages
    end
```

## What's declared vs. what's reachable

`traversal.py` declares 10 `OutcomeKind` values, but not all of them are active in runtime today. Checked against actual code paths, 7 are reachable and 3 are currently unused:

| Outcome | Reachable from | Status |
|---|---|---|
| `CONTINUE` | `step()`, `attempt_transition()`, `attempt_bridge()` | live |
| `ABSTAIN` | `step()`, `attempt_transition()`, `attempt_bridge()` | live |
| `COLLECT_EVIDENCE` | `step()`, `attempt_transition()` | live |
| `CHANGE_FRAME` | `step()` | live |
| `IDLE` | `step()` | live |
| `BRIDGE` | `step()` | live (advisory only) |
| `ESCALATE` | `attempt_bridge()` | live |
| `ASK` | — | declared, unreachable |
| `PUBLISH` | — | declared, unreachable |
| `REVISE_PLAN` | — | declared, unreachable |

This is not a bug. The underlying primitives already exist, but the traversal layer does not emit those outcomes yet. In simple terms: the types are there, the runtime wiring is not.

---

**prichindel.com** — v1.4.25
