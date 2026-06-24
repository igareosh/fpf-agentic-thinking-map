# FPF Source To Code Relation Audit

Purpose: sentence-scoped backlog for missing or compressed relations between the FPF source text and the current `fpf_thinking_map` code.

Rule for this artifact:
- Focus on relation coverage, not synonym coverage.
- Keep evidence close to the source sentence.
- Keep interpretation minimal.
- "Address" means "relation should be represented more explicitly or enforced more directly".

Sources audited in this pass:
- `FPF-Spec.md` (external; not included in this repository)
- Current code in `fpf_thinking_map/`

Legend:
- `missing` = relation not represented as a first-class structure or check
- `partial` = relation is hinted at but structurally compressed or under-enforced
- `wrong-shape` = relation exists but in a shape that contradicts source discipline

## Backlog

| ID | Status | Source lines | Source evidence | Code target | Address |
| --- | --- | --- | --- | --- | --- |
| R01 | wrong-shape | `FPF-Spec.md:1078-1150` | "`U.BoundedContext` is a `U.Holon`" and "declares a `U.Boundary`" | `primitives.py:23-35` | `ContextPrimitive` has no `holon` / `boundary` representation. Add explicit boundary-bearing shape or equivalent marker. |
| R02 | wrong-shape | `FPF-Spec.md:1100-1114` | "contexts do not form holarchies with each other" and "no is-a or containment relations" | `primitives.py:31` | `parent_context_id` encodes forbidden context containment/inheritance. Remove or replace with explicit bridge-based relation only. |
| R03 | partial | `FPF-Spec.md:1087-1096` | Context local constitution includes `Glossary`, `Invariants`, `Roles`, `Bridges` | `primitives.py:32-34` | `Roles` are not structurally attached to the context object, only globally indexed by `context_id`. Add direct local taxonomy attachment or explicit context-side role registry. |
| R04 | partial | `FPF-Spec.md:1093-1096` | Bridges carry explicit cross-context relations with "loss/fit notes" and congruence examples | `primitives.py:44-53` | `ContextBridge` has `translation_loss` but no fit / congruence level field. Add explicit fit relation carrier. |
| R05 | missing | `FPF-Spec.md:1118-1123` | "Any invariant authored in a Context applies only to holons and processes operating within that Context" | `primitives.py:33`, `state.py:267-305`, `traversal.py:112-209` | Invariants are stored as free-text strings but never evaluated or scoped as operational constraints. Add context-local invariant enforcement path. |
| R06 | partial | `FPF-Spec.md:1078-1086` | "Cross-context sameness is never inferred from spelling; alignment only via explicit Bridge artifacts" | `primitives.py:36-40`, `state.py:97-112` | Local glossary resolution exists, but no bridge-mediated term translation path is executable. Add bridge-aware relation lookup instead of local-only term resolution. |
| R07 | missing | `FPF-Spec.md:1122-1124` | "`U.RoleAssignment` references exactly one `U.BoundedContext` in its `context` field" | `state.py:35-54`, `state.py:142-153` | No `RoleAssignment` object exists; runtime binding of `actor_role_ids` cannot carry assignment-local context cardinality or issuance evidence. |
| R08 | missing | `FPF-Spec.md:1450-1456` | "`U.RoleAssignment` binds holder holon to role inside a bounded context, optionally within a time window" | `state.py:35-54`, `primitives.py:68-89` | Introduce first-class `RoleAssignment` primitive instead of binding roles directly on runtime input. |
| R09 | missing | `FPF-Spec.md:1452-1454`, `1508-1515` | "Separates that binding from `U.RoleEnactment`" and "`RoleEnactment ::= <work, by: RoleAssignment>`" | `primitives.py:102-121`, `state.py:79-80` | No enactment object or explicit `work -> role assignment` relation exists. Add enactment relation or equivalent reference field. |
| R10 | missing | `FPF-Spec.md:1481-1486` | "Behavioural roles: holder is a `U.System`" and "Status roles: holder is a `U.Episteme`" | `primitives.py:68-89`, `state.py:42-54` | No holder-kind eligibility model exists. Add holder kind and role kind checks. |
| R11 | missing | `FPF-Spec.md:1479-1480` | "`holder ∉ {U.Role, U.RoleAssignment}`" | `state.py:42-54`, `primitives.py:68-89` | No holder typing means this prohibition cannot be checked. Add typed holder binding and validation. |
| R12 | missing | `FPF-Spec.md:1486-1488` | "If `window` is present, enactments occur within it" | `state.py:35-54`, `primitives.py:102-121` | No assignment window or enactment time window discipline exists. Add assignment window and check it during work / transition decisions. |
| R13 | partial | `FPF-Spec.md:1495-1501` | "Authoritative" vs "Observational" role assignments have different gate effects | `guards.py:122-147`, `state.py:142-153` | Runtime roles are undifferentiated. Add assignment mode so guards can distinguish gate-opening authority from observational classification. |
| R14 | partial | `FPF-Spec.md:4627-4630` | "`≤` specialization MUST satisfy requiredRoles substitution" | `primitives.py:85` | Only one `specializes` pointer exists, but no expansion of `requiredRoles` or transition eligibility uses it. Add substitution evaluation path. |
| R15 | partial | `FPF-Spec.md:4632-4635` | "`⊥` overlapping windows on the same holder ... are ill-formed" | `primitives.py:84`, `guards.py:108-119` | Conflict is checked only as simultaneous active role IDs, not as overlapping assignments for the same holder and window. |
| R16 | missing | `FPF-Spec.md:4637-4641` | "`⊗` bundle is satisfied iff simultaneous valid assignments for each conjunct role" | `primitives.py:68-89`, `guards.py:209-250` | No bundle operator exists. Add conjunctive role bundle representation and satisfaction check. |
| R17 | missing | `FPF-Spec.md:4706-4753` | Commitment required fields include `subject`, `modality`, `scope`, `validityWindow`, `referents`; optional `owedTo`, `adjudication`, `source` | `primitives.py:137-154` | `CommitmentPrimitive` lacks `subject`, `referents`, `owed_to`, `source`; current shape is too compressed for source commitment semantics. |
| R18 | partial | `FPF-Spec.md:4694-4704` | Commitment must keep "accountable subject explicit" and not assign agency to descriptions | `primitives.py:137-154`, `logic.py:205-213` | Current commitment checks reduce commitment to evidence completion. Add explicit accountable subject relation distinct from evidence satisfaction. |
| R19 | missing | `FPF-Spec.md:4697-4701` | "Conflicts can be represented" | `primitives.py:137-154`, `logic.py:30-260` | No commitment conflict / contradiction relation exists beyond generic rule exclusivity. Add explicit commitment conflict channel if commitments are to remain source-faithful. |
| R20 | missing | `FPF-Spec.md:4990-5070` | "`U.SpeechAct` is a `U.Work` occurrence whose primary effect is communicative" | `primitives.py:96-121` | `WorkKind` only has `PLAN` and `ENACTMENT`. Add communicative / operational / epistemic work kinds or a speech-act subtype. |
| R21 | missing | `FPF-Spec.md:5033-5047` | `U.SpeechAct` carries `actTypes`, `addressedTo`, `utteranceRefs`, `carrierRefs`, `institutes` | `primitives.py:102-121`, `traversal.py:25-35` | No speech-act structure exists, so approvals / authorizations / revocations cannot be modeled as communicative work objects. |
| R22 | partial | `FPF-Spec.md:5015-5023` | "act can institute (or update/revoke) commitments, role assignments, statuses, etc., by reference" | `primitives.py:137-154`, `state.py:73-95` | No explicit "institutes / updates / revokes" relation exists between communicative work and commitments or assignments. |
| R23 | partial | `FPF-Spec.md:14540-14549`, `14602-14606` | Publication is typed projection `I→D→S` and "is not execution" | `primitives.py:305-319` | `PublicationPrimitive` is just a face record. Add projection lineage and explicit separation from work execution. |
| R24 | missing | `FPF-Spec.md:14580-14584` | EPV-DAG is "typed, acyclic" and "disjoint from mereology" | `primitives.py:250-265` | Evidence is flat; `supports` / `contradicts` do not encode typed DAG nodes or acyclicity. Add evidence graph structure, node kinds, and edge kinds. |
| R25 | missing | `FPF-Spec.md:14587-14589` | `verifiedBy` vs `validatedBy` are distinct anchor relations | `primitives.py:250-265` | Evidence model has no formal-vs-empirical anchor split. Add explicit anchor relation kind. |
| R26 | missing | `FPF-Spec.md:14590-14593`, `14641-14645` | `SCR` / `RSCR` emission and carrier resolution are mandatory for aggregate publication | `primitives.py:250-265`, `primitives.py:305-319` | No symbol carrier register structure exists. Add carrier register object or pinned carrier list structure. |
| R27 | missing | `FPF-Spec.md:14595-14599`, `14646-14649` | Design-time `MethodDescription` and run-time `Work` traces must not mix in one EPV-DAG instance | `primitives.py:102-121`, `primitives.py:250-265` | No explicit scope separation in evidence layer. Add node scope / relation type or distinct graphs. |
| R28 | missing | `FPF-Spec.md:14600-14602`, `14650-14652` | Evidencing `TransformerRole` must be external to the holon under evaluation | `primitives.py:250-265`, `guards.py:35-201` | No external-transformer relation exists for evidence production. Add evidencer identity and externality check. |
| R29 | partial | `FPF-Spec.md:14612-14617` | `Γ_method` run-time traces record `happenedBefore` and point to the `MethodDescription` they instantiate | `primitives.py:117`, `state.py:115-121` | `method_id` exists, but no ordered trace relation or method instantiation card exists. |
| R30 | missing | `FPF-Spec.md:15359-15425` | Strict distinction among `U.Role`, `U.Method`, `U.MethodDescription`, `U.Capability`, `U.WorkPlan`, `U.Work` | `primitives.py:96-121`, `state.py:66`, `state.py:79-80` | `WorkPrimitive(kind=PLAN)` compresses `WorkPlan` into `Work`, breaking source type separation. Split `WorkPlan` into distinct primitive. |
| R31 | missing | `FPF-Spec.md:15407-15418` | "`U.Work` is execution of a `U.MethodDescription` by a Holder acting under a `U.RoleAssignment`" | `primitives.py:102-121` | `WorkPrimitive` lacks holder / assignment / execution-chain structure strong enough for the canonical relation chain. |
| R32 | missing | `FPF-Spec.md:15420-15427` | Every `U.Work` declares `primaryTarget` and a kind: Operational / Communicative / Epistemic | `primitives.py:102-121` | Add `primary_target` and source-aligned work-kind taxonomy. |
| R33 | missing | `FPF-Spec.md:15464-15487`, `15609-15616` | Canonical relations include `performedBy`, `isExecutionOf`, `describes`, `bindsCapability` | `primitives.py:102-121`, `state.py:64-71` | These relations are only implicit via loose IDs, not represented as first-class links. |
| R34 | missing | `FPF-Spec.md:15398-15406`, `15588-15595` | `U.Method` and `U.MethodDescription` are distinct | `primitives.py:117` | `method_id` collapses method and method-description identity. Split into `method_id` and `method_description_id` or equivalent. |
| R35 | missing | `FPF-Spec.md:15401-15404` | `U.Capability` is an attribute of a `U.System` and distinct from work and method | `primitives.py:68-121`, `state.py:35-54` | No capability primitive or runtime capability check exists. |
| R36 | partial | `FPF-Spec.md:15549-16020` | `U.Work` includes dated occurrence, parameter bindings, resource consumption, outcomes, affected referent | `primitives.py:119-121` | Inputs/outputs exist, but no explicit occurrence window, resource ledger, affected referent, or acceptance outcome structure exists. |
| R37 | missing | `FPF-Spec.md:15700-15740` | CAC checks: context, assignment, standard | `state.py:194-216`, `traversal.py:211-260` | Transition and traversal checks cover context and evidence partially, but no explicit work acceptance against spec-standard chain exists. |
| R38 | missing | `FPF-Spec.md:15945-16018` | `U.WorkPlan` has planned windows, dependencies, intended performers, budgets, acceptance targets, variance dimensions | `primitives.py:102-121`, `state.py:66`, `guards.py:83-105` | Planning is treated as one `WorkPrimitive`; add dedicated `WorkPlan` / `PlanItem` structures and fulfilment / variance relations. |
| R39 | partial | `FPF-Spec.md:15983-16003` | Work may fulfil, partially fulfil, deviate from, or be unplanned against a plan item | `primitives.py:102-121`, `state.py:79-80` | No explicit `plannedAs` / fulfilment / variance relation exists between actual work and plan items. |
| R40 | wrong-shape | `FPF-Spec.md:20569-20605` | Gate decision lattice is `abstain ≤ pass ≤ degrade ≤ block` | `primitives.py:164-168`, `logic.py:168-177`, `traversal.py:246-255` | `GateDecision` lacks `BLOCK`, and `ABSTAIN` is used as blocked/fail-closed. Restore source lattice explicitly. |
| R41 | missing | `FPF-Spec.md:20605-20635` | `OperationalGate(profile)` and `GateCheckRef` / profile-bound folds are first-class | `primitives.py:171-218` | Gate model has checks but no gate profile, no fold policy object, no check references distinct from inline checks. |
| R42 | missing | `FPF-Spec.md:20636-20660` | Distinction between CV and GF is explicit in gate semantics | `primitives.py:188-218`, `guards.py:122-147` | No explicit CV/GF layer split exists. Add gate-evaluation dimension if source compliance matters. |
| R43 | missing | `FPF-Spec.md:20661-20730` | Gate system includes decision log, equivalence witness, scope merge semantics | `primitives.py:188-218`, `state.py:223-265` | Current gate evaluation returns only final decision and missing evidence. Add decision log / witness / merge trace if source relation should be preserved. |
| R44 | partial | `FPF-Spec.md:20569-20592` | Unknown / timeout / error folds are profile-bound, not hardcoded | `primitives.py:199-211` | `fail_closed` is a binary shortcut, not a source-style profile fold. |
| R45 | partial | `FPF-Spec.md:37026-37110` | MVPK is a typed/functorial projection over morphisms and "faces do not create new claims" | `primitives.py:305-319` | Current publication face enum preserves "no new semantics" in docstring but not as pinned constraints / lineage fields. |
| R46 | missing | `FPF-Spec.md:37080-37135` | Viewpoint and `U.PublicationScope` are explicit | `primitives.py:305-319` | Add viewpoint / publication-scope fields instead of only `face` + `audience`. |
| R47 | missing | `FPF-Spec.md:37136-37225` | Faces carry pins/refs, lawful orders, comparator sets, set-return semantics | `primitives.py:305-319`, `logic.py:287-318` | No comparator-set or pin discipline exists for publication outputs. |
| R48 | missing | `FPF-Spec.md:37190-37220`, `15760-15795` | Across-run comparisons forbid hidden scalarization and require declared comparator sets | `primitives.py:305-319`, `logic.py:227-240` | Risk and logic outputs are scalar/simple, but no publication comparison discipline exists. |
| R49 | partial | `FPF-Spec.md:14621-14623`, `37026-37225` | Publication / rendering / upload is work by an external transformer on carriers, cited in SCR | `primitives.py:305-319`, `primitives.py:102-121` | Publication object is detached from actual publication work and carriers. Add explicit publication-work anchor. |
| R50 | partial | `FPF-Spec.md:15549-16020`, `20569-20840` | Runtime should stay bite-sized, but semantic enforcement still depends on typed relations, not just string labels | `state.py:223-265`, `traversal.py:97-110` | Slice-first runtime is good horizontally, but the slice is still built from compressed primitives. Next pass should enrich primitives without widening prompt payload. |

## Lowest-friction next pass

These are the highest-value relation repairs that do not require widening the runtime chew:

1. Add first-class `RoleAssignment` and keep `actor_role_ids` as derived runtime convenience, not the semantic source of truth.
2. Split `WorkPlan` from `WorkPrimitive`; stop using `WorkKind.PLAN` as a substitute for the source distinction.
3. Restore gate lattice with explicit `BLOCK`; stop overloading `ABSTAIN` as the only hard denial outcome.
4. Add `primary_target`, source-aligned work kinds, and explicit `performedBy` / `isExecutionOf` references.
5. Add a minimal typed evidence graph layer with `verifiedBy` / `validatedBy` and external evidencer identity.
6. Remove `parent_context_id` or demote it out of kernel semantics; use bridges only for cross-context relation.
7. Add speech-act structure for communicative work that institutes / revokes commitments and assignments by reference.

## Notes

- This file is intentionally not a redesign document.
- It is a relation-coverage backlog for a follow-up pass.
- Source line spans are section-local evidence bands, not full formal proofs.
