# Decisions, Rejections, and Adoptions (Deep Technical Notes)

This file keeps theory-heavy and under-the-hood material away from mainstream entry docs.

Use this index when you need rationale and provenance behind design choices.

## Adoptions

- **A.15.5 Work-Entry Readiness (adopted):**
  - [FPF scope audit log](deep/FPF_SCOPE_AUDIT_LOG.md)
  - [FPF audit response](deep/FPF_AUDIT_RESPONSE.md)
- **Ignition Lock / Abort to Orbit — legal vs. fireable, and declared alternatives (adopted, v1.6.0):**
  - [ADOPTED_IGNITION_LOCK.md](deep/ADOPTED_IGNITION_LOCK.md)

## Expansions

- **Provenance — AuthorizationReceipt ("Clearance"), PendingInput/AWAIT ("Holding Pattern"), MoveIntent ("Tail Number"), and the authorization-clock fix, told as one arc (expansion, v1.7.0–1.9.1):**
  - [EXPANDED_PROVENANCE.md](deep/EXPANDED_PROVENANCE.md) — narrative; [CHANGELOG.md](../CHANGELOG.md) — version-by-version
  - [EXPANDED_PENDING_INPUT_AWAIT.md](deep/EXPANDED_PENDING_INPUT_AWAIT.md) — PendingInput/AWAIT detail, v1.8.0
  - [EXPANDED_MOVE_INTENT.md](deep/EXPANDED_MOVE_INTENT.md) — MoveIntent detail, v1.9.0
  - AuthorizationReceipt (v1.7.0) detail lives as the 2026-07-23 addendum in [IGNITION_LOCK_WIND_TUNNEL.md](deep/IGNITION_LOCK_WIND_TUNNEL.md) — it closes a gap that document named, so it's recorded there rather than a separate file

## Accepted, implementation pending

- **Traversal Checkpoint and Restore — faithful serialize/restore of `ActiveState`, map fingerprinting (accepted, not yet built):**
  - [DESIGN_TRAVERSAL_CHECKPOINT.md](deep/DESIGN_TRAVERSAL_CHECKPOINT.md)

## Rejections

- **Mandatory Orientation Projection in Every View (rejected):**
  - [REJECTED_ORIENTATION_VIEW_PROJECTION.md](deep/REJECTED_ORIENTATION_VIEW_PROJECTION.md)
- **Runtime Affordance Projection (rejected):**
  - [REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md](deep/REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md)
- **C.32 Candidate-Synthesis Logic (rejected):**
  - [REJECTED_C32_CANDIDATE_SYNTHESIS.md](deep/REJECTED_C32_CANDIDATE_SYNTHESIS.md)
- **NQD/OEE/Cultural Evolution family (rejected):**
  - [REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md](deep/REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md)
- **F.17 Unified Term Sheet (rejected):**
  - [REJECTED_F17_UNIFIED_TERM_SHEET.md](deep/REJECTED_F17_UNIFIED_TERM_SHEET.md)
- **A.22.CGUS as model self-admissibility procedure (rejected as practice; pattern acknowledged):**
  - [REJECTED_A22_CGUS_MODEL_SELF_ADMISSIBILITY.md](deep/REJECTED_A22_CGUS_MODEL_SELF_ADMISSIBILITY.md)

## Analysis and rationale

- **Why this package exists / compile rationale:**
  - [WHY_THIS_EXISTS.md](deep/WHY_THIS_EXISTS.md)
- **Token/cost methodology:**
  - [TRIPLE_TAX_CALCULUS.md](deep/TRIPLE_TAX_CALCULUS.md)
- **Reflections and design notes:**
  - [REFLECTIONS.md](deep/REFLECTIONS.md)
- **Source mapping and relation audit:**
  - [SOURCES.md](deep/SOURCES.md)
  - [FPF_SOURCE_TO_CODE_RELATION_AUDIT.md](deep/FPF_SOURCE_TO_CODE_RELATION_AUDIT.md)
- **Integrator advisories:**
  - [ADVISORIES.md](deep/ADVISORIES.md)
- **Architecture-level walkthrough:**
  - [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Related work comparisons:**
  - [RELATED_WORK_MILTONIAN_PRINCIPLES.md](deep/RELATED_WORK_MILTONIAN_PRINCIPLES.md)
  - [RELATED_WORK_GOFLOW_FPF_SKILL.md](deep/RELATED_WORK_GOFLOW_FPF_SKILL.md)

## Positioning

Mainstream files (especially root `README.md`) stay concise and runtime-focused.
This file is the single entrypoint for deeper theory, analyses, and historical decision records.
