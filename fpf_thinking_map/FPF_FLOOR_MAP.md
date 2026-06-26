# FPF Semantic Floor Map

Vertical amplification levels derived from FPF spec section layering.
Each floor defines a TTL range for evidence decay during agentic traversal.

The elevator has 5 floors. Evidence at each floor decays at the rate defined by that floor's base TTL. The hop counter (step_count) increments each `step()` call and drives the decay.

## Floor definitions

| Floor | Name | Base TTL | Decay formula | FPF sections |
|-------|------|----------|---------------|-------------|
| 0 | STRUCTURAL | None (infinite) | Never during traversal | A.1.1, A.2, A.3.3, A.6.9, A.21 defs |
| 1 | BINDING | 10 steps | Fixed: 10 | A.2.1, A.2.8, A.15.2 |
| 2 | EVIDENTIARY | 8 × F × R | `max(1, round(F × R × 8))` | A.10, B.3, B.3.4 |
| 3 | OPERATIONAL | 2 steps | Fixed: 2 | A.2.9, A.15.1, A.21 eval |
| 4 | PUBLICATION | None (inherited) | Source-dependent | E.17 |

## FGR-modulated decay (Floor 2)

At the EVIDENTIARY floor, the FGR trust tuple directly determines TTL:

```
computed_ttl = max(1, round(formality × reliability × 8))
```

The scope (G) dimension is not used in TTL — it measures claim breadth, not temporal stability.

| F (formality) | R (reliability) | Computed TTL | Example |
|--------------|----------------|-------------|---------|
| 1.0 | 1.0 | 8 | Formal proof from authoritative source |
| 0.8 | 0.9 | 6 | CI test results from reliable pipeline |
| 0.7 | 0.8 | 4 | Peer review from known reviewer |
| 0.5 | 0.5 | 2 | Manual test, moderate confidence |
| 0.3 | 0.4 | 1 | Anecdotal report, untested source |
| 0.2 | 0.3 | 1 | Hearsay (floor: always at least 1) |

## Decay timeline

When evidence age reaches TTL boundaries:

```
age < TTL           → CURRENT  (guard allows)
TTL ≤ age < 2×TTL   → STALE    (guard warns)
age ≥ 2×TTL          → EXPIRED  (evidence dead)
```

Example for OPERATIONAL evidence (TTL=2):
```
Step 0: added     → CURRENT
Step 1:           → CURRENT
Step 2: age=TTL   → STALE  (guard: "evidence is stale")
Step 3:           → STALE
Step 4: age=2×TTL → EXPIRED
```

Example for EVIDENTIARY evidence with F=0.8, R=0.9 (TTL=6):
```
Step 0: added      → CURRENT
Step 5:            → CURRENT
Step 6: age=TTL    → STALE
Step 11:           → STALE
Step 12: age=2×TTL → EXPIRED
```

## Primitive → Floor mapping

### Floor 0: STRUCTURAL — the building itself

| Primitive | FPF source | Why this floor |
|-----------|-----------|---------------|
| ContextPrimitive | A.1.1 U.BoundedContext | Meaning frames are build-time. Changing a context mid-traversal changes the board. |
| ContextBridge | A.6.9 CrossContextSameness | Bridge topology defines what cross-context moves are possible. Structural. |
| RolePrimitive | A.2 Role Taxonomy | Role definitions (responsibilities, conflicts, specialization) require governance to change. |
| TransitionPrimitive | A.3.3 U.Dynamics | State machine topology is compiled. Adding/removing transitions = redesigning the board. |
| GatePrimitive (definition) | A.21 GateProfilization | Gate structure (what checks, what evidence required) is build-time. |
| GateCheck (definition) | A.21 GateProfilization | Individual check definitions are structural. |

### Floor 1: BINDING — session-stable, can expire

| Primitive | FPF source | Why this floor |
|-----------|-----------|---------------|
| RoleAssignment | A.2.1 U.RoleAssignment | Assignments have validity windows (valid_from/valid_until). They bind a holder to a role for a period. |
| CommitmentPrimitive | A.2.8 U.Commitment | Obligations persist until revoked or expired. Deontic validity windows. |
| WorkPlanPrimitive | A.15.2 U.WorkPlan | Plans go stale as circumstances evolve. FPF A.4: "planning ≠ enactment" — plans are intent, not fact. |

### Floor 2: EVIDENTIARY — decays with trust (FGR-modulated)

| Primitive | FPF source | Why this floor |
|-----------|-----------|---------------|
| EvidencePrimitive | A.10 Evidence Graph | FPF B.3.4 explicitly: "evidence decays." Freshness is a first-class property. |
| FGR trust tuple | B.3 Trust & Assurance | The trust assessment itself has a shelf life. High-formality evidence from reliable sources decays slower. |

### Floor 3: OPERATIONAL — per-step ephemeral

| Primitive | FPF source | Why this floor |
|-----------|-----------|---------------|
| SpeechActPrimitive | A.2.9 U.SpeechAct | Communicative acts are events. An approval is valid at the moment it was given; its scope may not cover future states. |
| WorkPrimitive | A.15.1 U.Work | Enactment records are historical fact, but their relevance to current decisions is ephemeral. "We deployed yesterday" ≠ "we can deploy now." |
| GatePrimitive (evaluation result) | A.21 gate result | A gate evaluation is valid at the step it was computed. Evidence may change next step. |

### Floor 4: PUBLICATION — inherited freshness

| Primitive | FPF source | Why this floor |
|-----------|-----------|---------------|
| PublicationPrimitive | E.17 MVPK | Views project lower floors. A publication's freshness = min(freshness of its source work). If the source evidence expired, the publication is stale. |

## Design notes

**Why scope (G) is not used in TTL**: scope measures how broad a claim is ("this test covers the whole API" vs "this test covers one endpoint"). Broad claims don't decay faster or slower — they're just bigger. Formality and reliability determine shelf life.

**Why STRUCTURAL has no TTL**: changing a context definition or a role taxonomy mid-traversal is a board redesign, not a step. If structural primitives change, the SemanticMap must be rebuilt. The hop counter is irrelevant.

**Why OPERATIONAL is 2, not 1**: a gate evaluation at step N might inform the decision at step N+1 (the agent evaluates, then acts). But by step N+2, the evaluation should be refreshed. Two steps gives the agent one move to act on the result.

**The elevator analogy**: the building can be any height (traversal can be any number of steps). But the elevator's capacity is fixed per floor. Evidence at Floor 3 expires after 2 steps regardless of building height. Evidence at Floor 0 never expires — it IS the building.

---

prichindel.com | 2026-06-26 | v1.1.1
