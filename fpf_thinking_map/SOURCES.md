# Sources and attribution

This package was built from two academic sources. Almost everything traces back to one of these. A small number of implementation-level mechanics do not — FPF specifies what evidence decay, role assignment, and communicative work *are*, not the concrete numeric or structural form a compiled runtime engine needs to actually run them. Those gaps are ours: documented explicitly in "What we invented" below, built within FPF's boundaries, not offered back as FPF vocabulary, and not a rewrite or reinterpretation of anything FPF already settles.

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
| `WorkPlanPrimitive` | A.15.2 U.WorkPlan | A schedule of intent, kept as its own type from `WorkPrimitive` — the type distinction IS the enforcement; a plan existing does not mean the work was executed. |
| `RoleAssignment` | A.2.1 U.RoleAssignment | The binding of a holder to a role inside a context, kept distinct from `RolePrimitive` (the role definition) and from role enactment (work done under the assignment). Can expire. |
| `SpeechActPrimitive` | A.2.9 U.SpeechAct | A communicative work occurrence — approval, authorization, revocation. Turns evidence IDs like "owner_approval" from magic strings into a checkable act: who approved, when, what it institutes, whether it's still valid. |
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

The full FPF spec is ~51,000 lines covering dozens of patterns across 7 parts (A through G). We extracted the objects and guard rules in the table above. Everything else in the spec (the full ontology, the mathematical formalism, the publication kit details, the SoTA harvesting, the ethics framework, the explore-exploit calculus) was left out intentionally. FPF is a transdisciplinary, all-encompassing specification; this package was never meant to copy it, and does not try to. It is a distillation of the small slice that changes what a model does on one runtime move, not a port.

### What we invented (not extracted from FPF)

One piece of this package is genuinely ours, not FPF's, and the line above used to claim otherwise. Recorded here instead of quietly folded into the table above, because pretending it traces to a spec section it does not trace to would be exactly the kind of self-deception this package's own guard design refuses to allow the model to get away with — no reason to allow it in our own documentation.

**`SemanticFloor`** (`primitives.py`) — a 5-tier vertical structure (`STRUCTURAL / BINDING / EVIDENTIARY / OPERATIONAL / PUBLICATION`) with concrete base-TTL constants (10, 8, 2 steps) that drives evidence decay. FPF's B.3.4 (Evidence Decay) establishes *that* evidence goes stale and *that* freshness matters — it does not hand down a five-tier hierarchy or those specific numbers. Grouping FPF sections into structural/binding/evidentiary/operational/publication tiers, and picking concrete decay rates for each, was an engineering decision made to close the gap between "evidence can go stale" (the concept FPF states) and "here is the actual number of steps before a guard should distrust this claim" (the mechanic a running engine needs). It is own know-how, built to serve this package's own pursued scope — a deterministic runtime engine — within FPF's boundaries: it uses FPF's own section citations as the grounding for which concepts sit at which tier, it does not contradict or attempt to amend anything FPF already settles, and it was never proposed back into FPF's own spec as shared vocabulary (see `REJECTED_F17_UNIFIED_TERM_SHEET.md` on why that kind of ecosystem-facing naming discipline does not apply to a single downstream package like this one).

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

## External references

Short notes, not incorporated into the package — background reading around FPF and adjacent efforts. Full categorized log (awareness / inspected / rejected / concluded, one verdict per item) in `FPF_SCOPE_AUDIT_LOG.md`.

- [fpf.sh/generated/patterns/E.4.FPF](https://fpf.sh/generated/patterns/E.4.FPF) — normative pattern distinguishing the FPF framework edition from its carriers (publication formats, skill packs, MCP services).
- [fpf.sh/work-packets](https://fpf.sh/work-packets) — FPF's own official method for agent use: bounded MCP retrieval of 3-8 pattern IDs per task, not compilation.
- [ailev.livejournal.com/1770224.html](https://ailev.livejournal.com/1770224.html) — FPF author's own writeup: FPF vs. classical upper ontologies, normative "what to think about" vs. descriptive "what exists."
- [github.com/miltonian/principles](https://github.com/miltonian/principles) — unrelated independent first-principles agent framework; see `RELATED_WORK_MILTONIAN_PRINCIPLES.md`.
- [community.openai.com — Principles Framework writeup](https://community.openai.com/t/principles-framework-generate-ai-agents-using-first-principles-reasoning/1045890) — author's own announcement of the above.
- [fpf.sh/generated/patterns/F.17](https://fpf.sh/generated/patterns/F.17) — Unified Term Sheet; evaluated and rejected, see `REJECTED_F17_UNIFIED_TERM_SHEET.md`.
- [fpf.sh/generated/patterns/I.2](https://fpf.sh/generated/patterns/I.2) — entry-point disambiguation annex; validates this package's design bet (compile the FPF-pattern-selection work once, by a human, instead of asking the model to disambiguate at runtime).
- [fpf.sh/generated/patterns/E.23](https://fpf.sh/generated/patterns/E.23) — Quality Improvement Loop Method: disciplines agentic retry loops (re-evaluation, cost/risk, stop conditions). Not needed here — `step()` runs once per call with zero LLM calls inside the package; there is no loop in the runtime path for E.23's discipline to attach to.
- [fpf.sh/generated/patterns/E.20](https://fpf.sh/generated/patterns/E.20) — Mechanism Introduction Protocol: governs how FPF's own maintainers add mechanisms to the FPF kernel itself (still Draft status). Wrong actor, not scope — every locus it governs lives inside `ailev/FPF`; nothing in it addresses downstream consumers.

## Package authorship

- **Adaptation**: prichindel.com
- **Created**: 2026-06-24
- **Purpose**: Semi-encode FPF into an agentic thinking map with propositional logic glue
- **Repository**: [github.com/igareosh/fpf-agentic-thinking-map](https://github.com/igareosh/fpf-agentic-thinking-map)
