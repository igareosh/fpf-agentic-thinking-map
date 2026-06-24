# FPF Source-to-Code Relation Audit — Response

Reviewer: Felix (developer, Claude Code)
Date: 2026-06-24
Input: `FPF_SOURCE_TO_CODE_RELATION_AUDIT.md` (50 items from OpenAI pass)

## Summary verdict

The audit is accurate. All 50 items are real findings — no false positives. The question is which ones to fix, which to accept as intentional compression, and which to defer.

The guiding principle: **this package is a compiled thinking map, not a FPF reimplementation**. We extracted 8 objects from a 51k-line spec. Every compression was a conscious trade: less fidelity to the source, more usability for a mid-tier model chewing a per-move slice.

The audit correctly identifies where compression crossed into **wrong-shape** (we said something the spec forbids) vs **missing** (we left something out). Wrong-shape must be fixed. Missing is a judgment call.

---

## Category 1: Fix now (wrong-shape or high-value missing, no runtime bloat)

These items either violate the source spec in a way that produces incorrect behavior, or are cheap to fix without widening the per-step chew.

| ID | What | Why fix | How |
|----|------|---------|-----|
| **R02** | `parent_context_id` encodes forbidden context containment | The FPF spec explicitly says "contexts do not form holarchies with each other." Our field contradicts this. | **Remove `parent_context_id` from `ContextPrimitive`.** Cross-context relation goes through bridges only. |
| **R40** | Gate lattice missing `BLOCK`; `ABSTAIN` overloaded as both "insufficient info" and "hard denial" | Source gate lattice is `abstain ≤ pass ≤ degrade ≤ block`. Our `ABSTAIN` conflates two distinct outcomes. | **Add `GateDecision.BLOCK` to the enum.** `ABSTAIN` = insufficient evidence (can be resolved). `BLOCK` = hard denial (cannot proceed). Update gate evaluation and guards. |
| **R30** | `WorkPrimitive(kind=PLAN)` compresses `WorkPlan` into `Work` | Source explicitly separates `U.Work` (occurrence) from `U.WorkPlan` (intent). Our `WorkKind` enum masks a real type distinction. | **Split into `WorkPrimitive` (enactment only) and `WorkPlanPrimitive` (planning only).** Drop `WorkKind` enum — the type IS the distinction. |
| **R05** | Context invariants stored but never enforced | Invariants are strings that nothing reads. They exist in the prompt state but are not checked by guards or logic. | **Add invariant-check guard** that evaluates invariant expressions against the current state. Even if invariants stay semi-formal (strings the LLM evaluates), they should at least appear in the guard/logic path, not just in the glossary dump. |

## Category 2: Fix next round (genuine gaps, but require design thought)

These items are real structural absences. Fixing them adds value but requires deciding on shape. Queue for next pass.

| ID | What | Why next round | Shape sketch |
|----|------|---------------|-------------|
| **R07/R08** | No first-class `RoleAssignment` — roles bound directly via runtime IDs | The audit is right: FPF has `U.RoleAssignment` as a distinct object that binds holder to role inside a context with a time window. Our `actor_role_ids` is a shortcut. | Add `RoleAssignment` dataclass with `holder_id`, `role_id`, `context_id`, `window`. `RuntimeBinding` references assignments, not raw role IDs. `active_roles` resolves from assignments. |
| **R09** | No `RoleEnactment` — work doesn't reference the assignment it was performed under | Source says `RoleEnactment ::= <work, by: RoleAssignment>`. Our `WorkPrimitive.actor_role_id` is a loose string, not a reference to an assignment. | When R07/R08 land, add `performed_under: str` (assignment ID) to `WorkPrimitive`. |
| **R17** | `CommitmentPrimitive` lacks `subject`, `referents`, `owed_to`, `source` | Source commitment is richer: accountable subject, who it's owed to, what it refers to, where it came from. Our version only has modality + evidence refs. | Add fields. These don't widen per-step chew because commitments are only consulted when explicitly in scope. |
| **R20/R21** | No speech-act structure for communicative work | Source has `U.SpeechAct` as a `U.Work` subtype for approvals, authorizations, revocations. We have no way to model "approval as a communicative act that institutes a commitment." | Add `SpeechActPrimitive` as a `WorkPrimitive` subtype with `act_types`, `addressed_to`, `institutes`. Only enters the path when the current move is communicative. |
| **R32** | `WorkPrimitive` lacks `primary_target` and source-aligned work kinds | Source distinguishes Operational / Communicative / Epistemic work kinds and requires a primary target. | Add `work_kind` (operational/communicative/epistemic) and `primary_target` fields. |
| **R24/R25** | Evidence is flat — no typed DAG, no `verifiedBy` vs `validatedBy` distinction | Source evidence graph has typed nodes, edges, and a formal-vs-empirical anchor split. Ours is `supports: list[str]`. | Add `EvidenceEdge` dataclass with `kind` (supports/contradicts/verifies/validates) and build a minimal graph. Keep the evidence primitive itself flat; the graph is a separate structure on `SemanticMap`. |

## Category 3: Accept as intentional compression (do not fix)

These items are correctly identified as missing, but adding them would turn the thinking map into a FPF reimplementation. The compression is the feature.

| IDs | What | Why keep compressed |
|-----|------|-------------------|
| **R01** | `ContextPrimitive` is not a `U.Holon` with a `U.Boundary` | The holonic foundation is FPF's deepest abstraction layer. We don't need Entity → Holon → System/Episteme for a thinking map. Context-as-bounded-frame is sufficient. |
| **R03** | Roles not structurally attached to context object | Roles are indexed by `context_id` globally, and `active_roles` validates context match at runtime. Attaching a role registry directly to the context object would duplicate the `SemanticMap.roles` dict. The runtime behavior is correct. |
| **R04** | Bridge lacks `fit/congruence` field | `translation_loss` is sufficient for the current use case. Adding a formal congruence level adds semantic weight without operational benefit in the thinking map. |
| **R06** | No bridge-mediated term translation path | Bridge-aware term lookup is a RAG/retrieval feature, not a thinking map feature. The map tells the LLM that a bridge exists and what the loss is; the LLM does the translation. |
| **R10/R11** | No holder-kind eligibility model | FPF's distinction between System holders (behavioral roles) and Episteme holders (status roles) is deep ontology. The thinking map doesn't need to type-check holders; it needs to check role conflicts and context scope. |
| **R12** | No assignment window / time discipline | Time windows are important in FPF for formal role lifecycle. In the thinking map, temporal validity is handled by evidence freshness and external constraints, not by role assignment windows. |
| **R13** | Authoritative vs observational role assignments | This distinction matters in formal FPF gate semantics. In the thinking map, the guard layer handles gate authority via the gate-transition binding, not via role assignment modes. |
| **R14** | `specializes` pointer not used for `requiredRoles` substitution | Role substitution is FPF's formal role algebra. The thinking map checks conflict (⊥) which is the operationally critical case. Specialization substitution is a vertical enrichment. |
| **R15** | Conflict checked as simultaneous IDs, not overlapping assignment windows | Same as R12 — window discipline is deferred. ID-based conflict check catches the operational case. |
| **R16** | No bundle operator (⊗) | Role bundles are formal role algebra. The thinking map supports multi-role binding via `actor_role_ids` and checks conflicts. Bundles add formalism without operational payoff at this level. |
| **R18** | Commitment checks reduce to evidence completion | Source wants accountable subject distinct from evidence. For the thinking map, evidence-backed commitment is the operational check. Subject accountability is a governance layer concern. |
| **R19** | No commitment conflict channel | The logic layer's `exclusive_with` handles action contradictions. Formal commitment-level conflict requires the richer commitment model from R17. |
| **R22** | No "institutes/updates/revokes" relation | This is the speech-act machinery from R20/R21. Deferred to that implementation. |
| **R23** | Publication is "just a face record" | Intentional. Publication is out of the step path. Adding projection lineage turns it into a rendering engine. |
| **R26** | No symbol carrier register (SCR/RSCR) | Deep FPF publication machinery. Not needed for a thinking map. |
| **R27** | No scope separation between design-time and run-time evidence | Good formal discipline, but the thinking map's evidence is always runtime (current_evidence). Design-time evidence doesn't enter the per-step path. |
| **R28** | No external-transformer relation for evidence production | Important in FPF for audit trails. The thinking map trusts evidence IDs as given by the binding. Externality is a governance concern. |
| **R29** | No ordered trace or method instantiation card | `method_id` is a loose pointer. For the thinking map, this is sufficient — the model doesn't need to reconstruct method instantiation chains per step. |
| **R31/R33** | Work lacks `performedBy`, `isExecutionOf` as first-class links | These are source canonical relations. The thinking map uses loose IDs (`method_id`, `actor_role_id`). First-class links would be the right shape after R07/R08/R09 land. |
| **R34** | `method_id` collapses method and method-description | FPF's Method/MethodDescription distinction. For the thinking map, a method reference is enough. |
| **R35** | No capability primitive | `U.Capability` is a system attribute in FPF. The thinking map checks role eligibility and gate passage, not capability declarations. |
| **R36** | Work lacks occurrence window, resource ledger, acceptance outcome | Full work record semantics. The thinking map tracks inputs/outputs and evidence refs. Detailed occurrence tracking is an execution engine concern. |
| **R37** | No work acceptance against spec-standard chain | CAC (Context-Assignment-Standard) checks are formal FPF acceptance. The thinking map's guards cover context and evidence, not spec-standard chains. |
| **R38** | `WorkPlan` lacks dependencies, budgets, variance dimensions | Full planning semantics. Deferred to R30 split, but detailed planning fields are execution-engine scope. |
| **R39** | No `plannedAs` / fulfilment / variance relation | Depends on R30 (WorkPlan split). Deferred. |
| **R41/R42/R43/R44** | Gate model lacks profiles, CV/GF split, decision logs, fold policies | Deep gate semantics. The thinking map's gate model (checks → tri-state → decision) covers the operational case. Profile-bound folds and decision logs are audit-trail features. |
| **R45/R46/R47/R48/R49** | Publication lacks viewpoints, pin discipline, comparator sets, publication-scope | Deep MVPK semantics. Publication is intentionally thin in the thinking map — it's a face label, not a rendering engine. |
| **R50** | Slice-first runtime is built from compressed primitives | Correct observation. This is the design: compressed primitives → small slices → usable per-step chew. Enriching primitives is the next pass (Category 2), but only fields that don't widen the slice. |

---

## Scorecard

| Category | Count | Action |
|----------|-------|--------|
| Fix now (wrong-shape or cheap high-value) | 4 items (R02, R05, R30, R40) | Implement this round |
| Fix next round (genuine gaps, need design) | 6 items (R07/R08, R09, R17, R20/R21, R24/R25, R32) | Queue with shape sketches |
| Intentional compression (keep as-is) | 40 items | Document as design decisions |

---

SIGNED: Developer (Felix) | Claude Code context | 2026-06-24 | FPF audit response
