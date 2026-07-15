# FPF scope audit log

A running log of every FPF-ecosystem pattern, repo, or writeup checked against this package's scope. Different artifact from `FPF_SOURCE_TO_CODE_RELATION_AUDIT.md` (which audits line-level fidelity between the FPF spec and this code) — this one audits *external* patterns and prior art discovered after the fact, and records a verdict for each: awareness, inspected, rejected, or concluded. Nothing here changes without a verdict recorded.

## Rejected

Evaluated for inclusion, explicitly not incorporated. Full reasoning in the linked doc.

| Item | Verdict | Doc |
|---|---|---|
| C.32 Candidate-Synthesis Logic | Generative/branch-friendly — opposite of a convergent per-move constraint engine | `REJECTED_C32_CANDIDATE_SYNTHESIS.md` |
| NQD/OEE Cultural Evolution | Same failure shape as C.32 — widens the decision space instead of narrowing it | `REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md` |
| [F.17](https://fpf.sh/generated/patterns/F.17) — Unified Term Sheet | Wrong scale — governs cross-project term reuse at ecosystem scope; this is one terminal package, not many teams sharing vocabulary | `REJECTED_F17_UNIFIED_TERM_SHEET.md` |

## Inspected — no gap found

Read in full, checked against this package's actual code or design, no change needed. Verdict recorded in `SOURCES.md` § External references unless noted.

| Item | Verdict |
|---|---|
| [E.4.FPF](https://fpf.sh/generated/patterns/E.4.FPF) — Form and Publication-or-Access Carrier Assembly | Confirms this package's own framing: a carrier/downstream artifact, not an alternate FPF edition |
| [I.2](https://fpf.sh/generated/patterns/I.2) — Expanded Entry Disambiguation Cases | Validates the design bet — FPF's own eight-case disambiguation annex confirms pattern-selection-from-raw-spec is genuinely hard; this package does that work once, at compile time, instead of asking the model to do it live |
| [E.23](https://fpf.sh/generated/patterns/E.23) — Quality Improvement Loop Method | Doesn't apply — governs disciplined agentic retry loops; this package has zero LLM calls and zero retry inside the runtime engine (`step()` runs once per call, `demo_walk()` is a non-LLM test harness only). No loop exists for E.23's discipline to attach to |
| [E.20](https://fpf.sh/generated/patterns/E.20) — Mechanism Introduction Protocol | Wrong actor, not scope — governs how FPF's own maintainers edit the FPF kernel itself; nothing in it addresses downstream consumers |

## Inspected — gap found and closed

| Item | Finding | Fix |
|---|---|---|
| [F.8](https://fpf.sh/generated/patterns/F.8) — Mint-or-Reuse Decision | Naming discipline itself held up (every primitive traces to a cited FPF section) — but auditing against it surfaced that `SOURCES.md` undercounted the package's own primitives (3 missing from the table, all correctly cited in code) and overclaimed "nothing was invented" when `SemanticFloor`'s 5-tier TTL structure is genuine engineering synthesis, not FPF text | `SOURCES.md` — missing primitives added to the table; new "What we invented" section documents `SemanticFloor` explicitly as ours, grounded in but not extracted from FPF B.3.4 |

## Related work / prior art

Independent efforts in the same problem space, acknowledged, not incorporated (no code overlap).

| Item | Relationship | Doc |
|---|---|---|
| [goflowspace/goflow](https://github.com/goflowspace/goflow) | Independent decomposition of the same FPF spec — prompt-time reference library the model self-evaluates against, opposite bet from this package's deterministic guards | `RELATED_WORK_GOFLOW_FPF_SKILL.md` |
| [miltonian/principles](https://github.com/miltonian/principles) + its [OpenAI Community writeup](https://community.openai.com/t/principles-framework-generate-ai-agents-using-first-principles-reasoning/1045890) | Unrelated first-principles agent framework (no shared lineage with FPF). Its research-pilot benchmark independently reproduces this package's `WHY_THIS_EXISTS.md` thesis: v1 of their compiled pipeline *lost* to the bare model, from unverified framework scaffolding | `RELATED_WORK_MILTONIAN_PRINCIPLES.md` |

## Awareness only

Read, understood, informs context, no doc-level action taken beyond the entries above.

| Item | Why it matters |
|---|---|
| [fpf.sh/work-packets](https://fpf.sh/work-packets) | FPF's own official method for agent use — bounded MCP retrieval of 3-8 pattern IDs per task. Same architectural family as goflow (retrieval + model self-evaluation), the more radical position relative to what FPF's own team recommends is this package's, not theirs |
| [ailev.livejournal.com/1770224.html](https://ailev.livejournal.com/1770224.html) | FPF author's own writeup: FPF vs. classical upper ontologies, normative "what to think about" vs. descriptive "what exists." Confirms `EvidencePrimitive`/F-G-R was the right primitive to extract — the author names U.Reliability as FPF's own headline distinction |

## Verdict summary

Every item above resolves to exactly one of: **rejected** (3), **inspected, confirmed correct** (4), **inspected, found and fixed a real gap** (1), **acknowledged prior art** (2), **background awareness** (2). Twelve items total, one open thread closed each time — see `REFLECTIONS.md` for the standing design position this whole log keeps confirming: compile the framework away, once, rather than let the model carry it.

---

prichindel.com | 2026-07-10 | v1.4.13
