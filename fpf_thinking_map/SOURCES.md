# Sources and attribution

This package was built from two academic sources. Nothing was invented. Everything traces back to one of these.

## Source 1: FPF (First Principles Framework)

A transdisciplinary specification for reasoning, assurance, and evolution — an "operating system for thought."

- **Author**: Anatoly Levenchuk (with LLM assistance)
- **Repository**: [github.com/ailev/FPF](https://github.com/ailev/FPF)
- **Spec**: `FPF-Spec.md` (~51,000 lines) — not included in this repository; see the original repo
- **Status**: Normative kernel, "eternal alpha" — used in working projects
- **Prior Python model**: `py-fpf` in the original repo (basic graph model with CSV artifacts — not used directly, but informed the design)
- **Carrier vs. framework**: [E.4.FPF — Form and Publication-or-Access Carrier Assembly](https://fpf.sh/generated/patterns/E.4.FPF) — the normative pattern distinguishing the FPF framework edition from its carriers (publication formats, skill packs, MCP services, retrieval routes). This package is a carrier under that definition, not an alternate edition of FPF.

### What we took from FPF and where it is in the spec

| What we built | FPF spec section(s) | What the spec section defines |
|--------------|---------------------|------------------------------|
| `ContextPrimitive` | A.1.1 U.BoundedContext | A bounded area where words have specific local meanings. Cross-context use requires explicit bridges with declared translation loss. |
| `ContextBridge` | A.6.9 CrossContextSamenessDisambiguation | How to connect two contexts: direction, mapping, substitution license, loss notes. |
| `RolePrimitive` | A.2 Role Taxonomy, A.2.1 U.RoleAssignment, A.2.7 U.RoleAlgebra, A.13 AgentialRole | Roles as assignments (not identities). Specialization (≤), incompatibility (⊥), bundles (⊗). Agency as a spectrum (passive → deliberative). |
| `WorkPrimitive` | A.15 U.Planning, A.15.1 U.Work, A.15.2 U.WorkPlan | The strict distinction between a plan (intent) and an enactment (what actually happened). A plan is NOT done work. |
| `CommitmentPrimitive` | A.2.8 U.Commitment | Deontic obligations: MUST, SHOULD, MAY, MUST_NOT, SHOULD_NOT. Scoped, with validity windows and evidence refs. Separate from gates (deontic vs structural). |
| `GatePrimitive` | A.21 GateProfilization, A.19.UNM (tri-state guard) | Operational gates that aggregate checks. Four outcomes: abstain, pass, degrade, block. Fail-closed by default. |
| `EvidencePrimitive` | A.10 Evidence Graph, A.2.4 U.EvidenceRole, B.3 Trust & Assurance (F-G-R), B.3.4 Evidence Decay | Evidence with provenance. Trust is a computed tuple: Formality (how rigorous), scope (how broad), Reliability (how dependable). Evidence can go stale. |
| `TransitionPrimitive` | A.3.3 U.Dynamics, B.4 Canonical Evolution Loop, A.2.5 U.RoleStateGraph | State transitions with optional gate requirements and required evidence. The canonical loop: Run → Observe → Refine → Deploy. |
| `PublicationPrimitive` | E.17 MVPK Multi-View Publication Kit | Same content, different audiences: plain, technical, interop, assurance. Views do not add new semantics. |
| Guard: commitment evidence | A.2.8 + A.10 | Binding commitments (MUST/MUST_NOT) require evidence refs to be present. |
| Guard: plan ≠ enactment | A.4 Temporal Duality, A.7 Strict Distinction | Having a plan does not mean the work is done. Cannot transition to "done" without enactment records. |
| Guard: role conflict | A.2.7 U.RoleAlgebra (⊥) | Incompatible roles cannot be active at the same time. |
| Guard: gate pass | A.21 GateProfilization | Gate must pass (or at least degrade, not abstain/block) before a guarded transition fires. |
| Guard: scope check | A.2.6 USM (Unified Scope Mechanism) | Actions must stay within the active context. Cross-context action requires a bridge. |
| Guard: evidence freshness | B.3.4 Evidence Decay | Stale or expired evidence triggers a warning before decisions. |

### What we did NOT take from FPF

The full FPF spec is ~51,000 lines covering dozens of patterns across 7 parts (A through G). We extracted 10 objects and 9 guard rules. Everything else in the spec (the full ontology, the mathematical formalism, the publication kit details, the SoTA harvesting, the ethics framework, the explore-exploit calculus) was left out intentionally. This package is a distillation, not a port.

## Source 2: Computational logic lectures (Mitev L.)

A university lecture series on propositional logic. We took the 6 basic logic operators and the Wumpus World pattern for agent navigation.

- **Title**: "Bazele programarii logice" (Fundamentals of Logic Programming)
- **Author**: Mitev L.
- **Format**: 5 lecture PDFs (c1p through c5p)

### What each lecture covers and what we used

| Lecture | Topics | What we took |
|---------|--------|-------------|
| c1p | Propositions, 6 operators (NOT, AND, OR, XOR, IMPLIES, IFF), truth tables, operator precedence | All 6 operators as Python classes (`NotProp`, `AndProp`, `OrProp`, `XorProp`, `ImpliesProp`, `IffProp`). Truth table behavior is verified in `verify.py`. |
| c2p | Validity (tautology), satisfiability, unsatisfiability, contingency, consistency of proposition sets, system specifications | Consistency check in `LogicLayer.consistency_check()` — verifying that the set of fired rules does not contain contradictory actions. |
| c3p | Logical equivalences, De Morgan's laws, contrapositives, minimum connective sets | Informed the design that any complex condition can be built from NOT + one binary operator. We kept all 6 for readability. |
| c4p | Natural deduction (introduction/elimination rules for each operator), replacement rules | Not directly used in code, but informed the understanding of how each operator introduces or eliminates knowledge. |
| c5p | Semantic reasoning with truth tables, Wumpus World (propositional logic for AI agent navigation) | The core design pattern: an agent navigates a space, evaluates propositions about its surroundings at each step, and uses logic to determine safe/valid moves. Our "cells" = semantic states, "moves" = transitions, "percepts" = evidence/gate/commitment facts. |

### The Wumpus World pattern (from lecture 5)

In the Wumpus World, an agent explores a 4x4 grid. Each cell may contain a pit or a monster. The agent perceives clues (breeze = adjacent pit, stench = adjacent wumpus) and uses propositional logic to deduce which cells are safe before moving.

We applied the same pattern:
- The semantic map is the grid
- Evidence, gates, and commitments are the percepts
- Logic operators compose percepts into safety checks
- Guards are the hard constraints (like "don't walk into a known pit")
- The model picks moves from the safe set

## Package authorship

- **Adaptation**: prichindel.com
- **Created**: 2026-06-24
- **Purpose**: Semi-encode FPF into an agentic thinking map with propositional logic glue
- **Repository**: [github.com/igareosh/fpf-agentic-thinking-map](https://github.com/igareosh/fpf-agentic-thinking-map)
