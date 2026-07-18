# dev_mcp — visual architecture

Companion to the top-level [`ARCHITECTURE.md`](../ARCHITECTURE.md), scoped to the MCP
layer only — `dev_mcp` never appears in that diagram because it isn't shipped in the
PyPI package. This is what wraps the engine for agentic testing, not the engine itself.

## Tool surface

Seven tools, three jobs: read the docs, run code against the real engine, read back
what was durably logged from past runs.

```mermaid
graph LR
    subgraph DOCS["Docs (read-only, no engine touched)"]
        T1[get_fpf_source_mapping]
        T2[get_audit_gaps]
        T3[get_advisories]
    end

    subgraph RUN["Execution (touches the real engine)"]
        T4[run_scenario]
        T5[run_verify]
    end

    subgraph LOGS["Witness logs (read past runs back)"]
        T6[get_advisory_log]
        T7[get_compliance_log]
    end

    MCP([MCP client<br/>Cursor / Claude Code]) --> DOCS
    MCP --> RUN
    MCP --> LOGS

    T4 -.appends.-> T6
    T4 -.appends.-> T7

    style DOCS fill:#3a3a3a,color:#fff
    style RUN fill:#1a4a4a,color:#fff
    style LOGS fill:#1a3a5c,color:#fff
    style MCP fill:#2d5016,color:#fff
```

## `run_scenario` request lifecycle

Both awareness layers — advisory detection and compliance mode — are optional,
independent, and non-blocking. Neither can stop `exec(code)` from doing whatever it
does; they only get to look at what already happened, after it happened.

```mermaid
sequenceDiagram
    participant C as MCP client
    participant S as dev_mcp.server
    participant NS as exec namespace
    participant E as ThinkingMapTraversal
    participant AD as advisory_detectors
    participant CI as compliance_inspector
    participant LOG as .state/*.jsonl

    C->>S: run_scenario(code, scope, compliance_mode?)
    S->>NS: exec fpf_thinking_map imports
    alt compliance_mode=True
        S->>CI: wrap ThinkingMapTraversal (subclass, transparent)
        CI-->>NS: ns["ThinkingMapTraversal"] replaced
    end
    S->>NS: exec(code)
    NS->>E: attempt_transition() / attempt_bridge()
    E-->>NS: Outcome(kind=...) — the engine's own verdict
    opt compliance_mode=True
        NS->>CI: record {requested, expected, outcome, fit}
    end
    S->>AD: scan namespace for ActiveState / LogicLayer
    AD-->>S: advisories_triggered (or none)
    opt compliance_mode=True
        S->>CI: summary() — tally + address note
    end
    S->>LOG: append hits (best-effort, never raises)
    S-->>C: {result, stdout, advisories_triggered?, compliance?}
```

## Two witnesses, one engine — why neither one drives

The shape that makes `ADV-09` true isn't an accident of this diagram — it's the point
of it. Both witnesses sit *beside* the engine, read what it already decided, and hand
that back to whoever's calling. Neither one sits *in front of* it.

```mermaid
flowchart TD
    ENGINE["fpf_thinking_map<br/>stateless, domain-blind by design"]

    ENGINE -->|Outcome.kind| AD["advisory_detectors<br/>pattern: does this ActiveState<br/>sit in a known blind spot?"]
    ENGINE -->|Outcome.kind| CI["compliance_inspector<br/>fact: did this move get CONTINUE?"]

    AD -->|"advisories_triggered"| PAYLOAD
    CI -->|"compliance.address"| PAYLOAD

    PAYLOAD["run_scenario response"] --> MODEL(["whoever's driving —<br/>often the LLM itself"])

    MODEL -->|"decides what matters<br/>for its own domain"| DECISION["build a rail, or don't —<br/>dev_mcp doesn't get a vote"]

    style ENGINE fill:#2d5016,color:#fff
    style AD fill:#8b6914,color:#fff
    style CI fill:#1a3a5c,color:#fff
    style PAYLOAD fill:#3a3a3a,color:#fff
    style MODEL fill:#1a4a4a,color:#fff
    style DECISION fill:#5c1a1a,color:#fff
```
