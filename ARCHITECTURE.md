# Architecture

Visual scheme of the thinking map — how the pieces connect.

## Module dependency

```mermaid
graph LR
    P[primitives.py<br/>10 objects + 5 floors]
    S[state.py<br/>binding + active state + slice]
    G[guards.py<br/>9 hard constraints]
    L[logic.py<br/>6 operators + rules]
    T[traversal.py<br/>step engine + 10 outcomes]
    E[examples.py<br/>5 scenarios]
    V[verify.py<br/>19 checks]

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

```mermaid
flowchart TD
    START([step called]) --> INC[step_count++<br/>drives TTL decay]
    INC --> CTX{active<br/>context?}
    CTX -->|no| CF[CHANGE_FRAME]
    CTX -->|yes| XCTX{cross-context<br/>transition?}
    XCTX -->|yes| DENIED1[DENIED]
    XCTX -->|no| LOGIC[evaluate logic rules]
    LOGIC --> CONSIST{consistent?}
    CONSIST -->|contradiction| DENIED2[DENIED]
    CONSIST -->|ok| GUARDS[run 9 guards]
    GUARDS --> GPASS{all<br/>allow?}
    GPASS -->|deny + evidence path| CE1[COLLECT_EVIDENCE]
    GPASS -->|deny + no path| DENIED3[DENIED]
    GPASS -->|allow| EVCHECK{evidence<br/>gaps?}
    EVCHECK -->|gaps| CE2[COLLECT_EVIDENCE]
    EVCHECK -->|complete| TRANS{transitions<br/>available?}
    TRANS -->|yes| CONTINUE[CONTINUE<br/>+ slice + contract]
    TRANS -->|no + actions| CONTINUE2[CONTINUE]
    TRANS -->|no + bridges| BRIDGE[BRIDGE<br/>+ target contexts]
    TRANS -->|nothing| IDLE[IDLE<br/>at rest]

    style CF fill:#8b6914,color:#fff
    style DENIED1 fill:#8b1a1a,color:#fff
    style DENIED2 fill:#8b1a1a,color:#fff
    style DENIED3 fill:#8b1a1a,color:#fff
    style CE1 fill:#4a3728,color:#fff
    style CE2 fill:#4a3728,color:#fff
    style CONTINUE fill:#2d5016,color:#fff
    style CONTINUE2 fill:#2d5016,color:#fff
    style BRIDGE fill:#1a3a5c,color:#fff
    style IDLE fill:#3a3a3a,color:#fff
```

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

---

**prichindel.com** — v1.1.3
