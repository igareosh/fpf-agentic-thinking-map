# Advisories for integrators

Not defects. These are places where `fpf_thinking_map` deliberately stays minimal and leaves a real decision to whoever builds a domain map on top of it — `scope="user-extension"` territory, not something the publisher will fold into the core, because building it in would mean guessing your domain's actual requirement instead of you stating it explicitly.

Each advisory: what the default behavior actually is, why that's the default, and exactly how to get stricter behavior if your domain needs it.

**Read these two first if you read nothing else here: [`ADV-03`](#adv-03--active_context_id-is-self-asserted-not-verified-against-how-you-got-there) (context claims aren't verified) and [`ADV-07`](#adv-07--riskaboves-string-matching-is-case-sensitive-and-fails-silently) (a routing rule built exactly as this doc recommends can still silently do the opposite of what you intended). Both are silent — no error, no warning — and both sit directly behind paths this document itself tells you to use.**

**Testing against these directly?** [`dev_mcp`](../../dev_mcp/README.md)'s
`run_scenario` checks every one of the 8 auto-detected advisories below
against whatever `ActiveState` your scenario builds, automatically — no
need to reason by hand about whether your test case happens to sit in one
of these blind spots. Hits are returned inline and logged
(`get_advisory_log`), so you can tell which of these are theoretical for
your domain and which your own scenarios actually hit. `ADV-09` isn't part
of that automatic scan — see its own entry for why not.

## Index

| ID | Tag | One line |
|----|-----|----------|
| [`ADV-01`](#adv-01--evidence-staleness-warns-it-does-not-block) | staleness warns | Expired evidence still satisfies `required_evidence` — `WARN`, not `BLOCK` |
| [`ADV-02`](#adv-02--risk_level-doesnt-filter-transitions-on-its-own) | risk doesn't route | `risk_level` alone changes nothing about which transitions show up |
| [`ADV-03`](#adv-03--active_context_id-is-self-asserted-not-verified-against-how-you-got-there) | context is self-asserted | sharpest — nothing verifies you actually arrived where you claim to be |
| [`ADV-04`](#adv-04--contradiction-detection-is-opt-in-not-inferred-from-action-names) | contradictions are opt-in | opposite actions only clash if `exclusive_with` says so |
| [`ADV-05`](#adv-05--gate-degrade-only-distinguishes-partial-evidence-within-a-single-gatecheck) | DEGRADE needs grouping | split evidence across checks and `DEGRADE` can never fire |
| [`ADV-06`](#adv-06--agency_level-is-descriptive-metadata-not-an-enforced-permission) | agency isn't enforced | `PASSIVE` and `DELIBERATIVE` fire the same transitions unless you gate it |
| [`ADV-07`](#adv-07--riskaboves-string-matching-is-case-sensitive-and-fails-silently) | case-sensitive risk | sharpest — `"CRITICAL"` silently reads as `"normal"`, no error |
| [`ADV-08`](#adv-08--no-persistence-surface-session-continuity-is-a-harness-responsibility-not-an-engine-one) | no persistence | no `to_dict`/`from_dict` anywhere — session continuity is the harness's job |
| [`ADV-09`](#adv-09--compliance-mode-is-a-witness-not-a-fix--and-cant-be-one-without-knowing-your-domain) | **no oracles, no future seers** | compliance mode can show you drift, it cannot know your domain well enough to fix it |

---

## ADV-01 — Evidence staleness warns, it does not block

**What**: evidence past its TTL (`Freshness.EXPIRED`) still satisfies a transition's `required_evidence`. The engine computes and reports the expiry accurately — `effective_freshness()`, `ttl_remaining()` — and the guard layer raises a `WARN` (`"Evidence '...' is expired"`), but a `WARN` never blocks a move. Only `DENY` (guard) or `BLOCK`/`ABSTAIN` (gate) do.

**Why this is the default**: the library doesn't know whether staleness should be advisory or fatal for your domain. A support-ticket confirmation going stale after 48 hours might be fine to act on with a visible warning attached — a human can see it happened. A safety-critical sign-off going stale might need to hard-stop the transition entirely. Building either assumption into the core means guessing wrong for someone else's domain.

**How to get a hard block**: attach the evidence to the transition via a `GatePrimitive`/`GateCheck` instead of relying on bare `required_evidence` alone. Gate evaluation is where `ABSTAIN`/`BLOCK` live — write a guard or `LogicLayer` rule using `EvidenceFresh(...)` that checks freshness explicitly and drives the gate to `BLOCK` when the evidence is `EXPIRED`, not merely present.

---

## ADV-02 — `risk_level` doesn't filter transitions on its own

**What**: `possible_transitions` is scoped by `(context, current_state)` only. Setting `binding.risk_level = "critical"` doesn't remove or add any transitions — a `critical` and a `normal` binding see the identical transition list from the same state.

**Why this is the default**: risk-based branching is a domain policy, not a structural fact about the map. The library has no way to know which of your transitions should be risk-gated and which are risk-agnostic — that's a judgment call about your process, not fpf's to make.

**How to get risk-based routing**: use `LogicLayer` with a `RiskAbove(threshold)` proposition driving a `DecisionRule`, or a guard scoped to the specific transition, so the decision to allow, deny, or route by `risk_level` is computed by the engine — not left for the calling model to infer from a raw number it was handed and no instructions on what to do with it.

---

## ADV-03 — `active_context_id` is self-asserted, not verified against how you got there

**The sharpest one here — read this before trusting a bridge for anything security-adjacent.**

**What**: `RuntimeBinding.active_context_id` is plain input, fresh on every call. Nothing checks that a caller claiming to be in `"exec_queue"` actually arrived there via `attempt_bridge()`/`cross_bridge()`. Constructing a new binding with `active_context_id="exec_queue"` directly succeeds identically to crossing the licensed bridge — same `CONTINUE` outcome, no distinction, no record that the formal path was skipped.

**Why this is the default**: the engine is stateless per call — it has no session, no identity, no memory of a prior binding unless you hand it one (`ActiveState` objects can be reused across `step()` calls, but a *fresh* `build_active_state()` call has no way to know what came before it). `#26`'s bridge licensing (`substitution_license`, `translation_loss` vs. `risk_level`) governs the *transition function* `cross_bridge()` exposes — it was never a claim that the engine authenticates *how* a binding's `active_context_id` came to be what it is. That's a harness-level responsibility, not something a per-call traversal engine can enforce on its own.

**How to close the gap**: if which context an agent is "in" needs to be trustworthy, the calling harness must be the one enforcing continuity — persist the `ActiveState` object itself (or its `active_context_id`) across the session rather than reconstructing bindings from scratch on each call, and never accept an externally supplied `active_context_id` without validating it came from your own prior `cross_bridge()` call. This is the same shape as ADV-01/ADV-02: fpf computes the right answer when asked through the right door, but doesn't — can't — stop you from walking in the window.

---

## ADV-04 — Contradiction detection is opt-in, not inferred from action names

**What**: `LogicLayer.consistency_check()` only flags a contradiction between two `DecisionRule`s that explicitly declare each other via `exclusive_with`. Two satisfied rules recommending literally opposite actions (`"proceed"` vs. `"hold"`) produce no contradiction and no warning unless each rule's `exclusive_with` names the other's action.

**Why this is the default**: the engine has no semantic understanding of action strings — `"proceed"` and `"hold"` are opaque labels to it, not known opposites. Inferring opposition from string content would mean guessing at your domain's vocabulary; `exclusive_with` makes the domain author state the relationship explicitly instead.

**How to get it caught**: when two rules can fire on the same evidence and their actions are meant to be mutually exclusive, declare it both ways — `exclusive_with=["hold"]` on the rule that can produce `"proceed"`, `exclusive_with=["proceed"]` on the one that can produce `"hold"`. Confirmed working once declared: `step()` returns `ABSTAIN` with `"Logic contradiction: [...]"` in the reason.

---

## ADV-05 — Gate `DEGRADE` only distinguishes partial evidence within a single `GateCheck`

**What**: `GatePrimitive.evaluate()` returns `DEGRADE` only when at least one of its `GateCheck`s individually evaluates to `DEGRADE` — which only happens when *that check's own* `required_evidence` list has some, but not all, items present. A gate built from several single-evidence `GateCheck`s (one check per fact) can never produce `DEGRADE`: each check is binary (fully satisfied → `PASS`, or fully missing → `ABSTAIN`), so "one of three facts known" looks identical to "zero of three facts known" at the gate level — both `ABSTAIN`.

**Why this is the default**: `DEGRADE` is a property of a single check's internal completeness, not an aggregate computed across independent checks — aggregating "3 truths, 4 known, 1 missing" would require a policy choice (a threshold? a weighting?) the library isn't in a position to guess.

**How to get partial visible as `DEGRADE`**: group evidence that should be assessed together into *one* `GateCheck`'s `required_evidence` list (e.g. `GateCheck("tests", "...", required_evidence=["unit_tests_passed", "integration_tests_passed"])`) rather than splitting related facts across separate checks. Confirmed: none → `insufficient`, partial (one of two, grouped) → `partial`, full → `pass` — exactly distinguishable, but only with this grouping.

---

## ADV-06 — `agency_level` is descriptive metadata, not an enforced permission

**What**: `RolePrimitive.agency_level` (`PASSIVE` / `REACTIVE` / `AUTONOMOUS` / `DELIBERATIVE`) is surfaced to the model (`to_llm_prompt_state()`'s `active_roles[].agency`) but doesn't gate anything by default. A role bound as `PASSIVE` can fire the exact same transition as one bound `DELIBERATIVE` — identical `CONTINUE`, no distinction.

**Why this is the default**: same shape as `risk_level` (ADV-02) — whether "passive" should mean "cannot trigger this class of transition" is a domain policy question the primitive alone can't answer, because not every transition in every domain needs agency-gating.

**How to enforce it**: write a guard (or `LogicLayer` rule) scoped to the transitions that should be agency-gated, checking `state.active_roles` for the required `agency_level` before allowing the move — the same pattern as wiring risk-based routing in ADV-02.

---

## ADV-07 — `RiskAbove`'s string matching is case-sensitive and fails silently

**The other one to read before you ship. Following `ADV-02`'s own advice does not protect you from this.**

**What**: `RiskAbove(threshold)` compares `binding.risk_level` against a fixed internal table (`{"low": 0, "normal": 1, "high": 2, "critical": 3}`) via plain dict lookup — `self._levels.get(state.binding.risk_level, 1)`. Any string not found in that table, including a correctly-spelled value in the wrong case (`"CRITICAL"` instead of `"critical"`), silently resolves to `1` — the same numeric level as `"normal"`. There is no error, no warning, no `UNKNOWN` sentinel. A `DecisionRule` gated on `RiskAbove("critical")` will report `satisfied: False` for `risk_level="CRITICAL"` exactly as if the input had genuinely been low-risk.

Confirmed directly: a rule wired `condition=RiskAbove("critical"), action_if_true="escalate", action_if_false="queue"` returns `action: "escalate"` for `risk_level="critical"` and silently `action: "queue"` — the opposite decision — for `risk_level="CRITICAL"`. `consistency_check()` reports `consistent: True` in both cases; nothing in the outcome distinguishes a genuine low-risk case from a typo'd critical one.

**Why this is the default**: `risk_level` is a plain string on `RuntimeBinding`, not a validated enum — the primitive layer accepts any value a caller supplies, and `RiskAbove` was built to degrade gracefully (default to `1`/`"normal"`) rather than raise on unrecognized input, on the assumption that a missing/malformed risk signal should fail toward caution-as-normal rather than crash the traversal. That default-to-normal choice is defensible in isolation; it becomes dangerous specifically because it's silent and specifically because `ADV-02` recommends `RiskAbove` as *the* fix for risk-based routing without calling out that the string has to match exactly.

**How to close the gap**: normalize `risk_level` before it reaches the engine — lowercase and validate against the known set (`{"low", "normal", "high", "critical"}`) at the point where your harness constructs `RuntimeBinding`, and reject or log anything that doesn't match rather than letting it fall through to `RiskAbove`'s silent default. Do this at the boundary, once, rather than trusting every caller to spell `risk_level` correctly forever.

---

## ADV-08 — no persistence surface: session continuity is a harness responsibility, not an engine one

**What**: `ActiveState`, `RuntimeBinding`, and `MoveTrace` are plain `@dataclass` objects with no serialization surface — no `to_dict`/`from_dict`/`__getstate__`/`asdict` anywhere in `state.py`. There is no library-supported way to persist a session and hand it back to the engine later.

A harness that builds its own persistence anyway (pickling `RuntimeBinding` + `current_state`, reconstructing `ActiveState` on reload) will silently zero the stagnation counter (`#28`) on every reload. Its backing store — `_evidence_added_at`, `_state_visits`, `_state_visit_evidence` — is declared `init=False`: the dataclass constructor does not accept them as arguments. A naive rebuild produces a structurally valid `ActiveState` that has forgotten every prior visit. `visits_remaining` resets to full budget across exactly the boundary (idle resume, LLM context compaction, process restart) where a harness would most want it preserved.

**Why this is the default**: same shape as `ADV-03` — the engine is stateless per call, has no session concept, and persistence is a harness-owned decision the library can't make without guessing your storage layer (in-memory dict, Redis, disk, a database row keyed by conversation id — all legitimate, none of fpf's business to pick).

**How to close the gap**: this is not an engine feature to request — it's a decision for whichever harness wraps the engine (an MCP server, an agent runtime, a CLI loop). If your harness needs continuity across idle periods, LLM-side context compaction, or process restarts: persist `RuntimeBinding` + `current_state` + `trace` yourself, and if `#28`'s stagnation counter needs to survive that boundary too, reach into `_evidence_added_at`/`_state_visits`/`_state_visit_evidence` directly — not through the constructor, since they're `init=False` — and restore them explicitly. fpf's own contribution stops at keeping the re-injectable payload small enough to make this practical: `slice()` (measured ~481 tokens/decision) and `to_llm_prompt_state()` are both already scoped to the current move, not the whole map — carrying them across a persistence boundary is the harness's call to make, not fpf's to force.

---

## ADV-09 — Compliance mode is a witness, not a fix — and can't be one without knowing your domain

*Tag: no oracles, no future seers.*

**This one is a confession as much as an advisory.** Compliance mode was built trying to go further than a witness — the actual goal, while building it, was a real fix: turn "the model drifted from the map" into something that stops happening, not just something that gets noticed. It doesn't do that, and the honest reason isn't lack of engineering time, it's that no amount of engineering here would have closed it. Every path from "here's a drift" to "here's a fix" ran back into the same wall: we don't know if a given drift is a real problem or the map missing something legitimate, because we don't know what this is deployed into. We are not oracles of context. That's not a caveat on top of the advisory — realizing it mid-build is the actual origin of this advisory.

**What**: `dev_mcp`'s compliance mode (`run_scenario(..., compliance_mode=True)`, see `dev_mcp/compliance_inspector.py`) records every `attempt_transition()`/`attempt_bridge()` call's own verdict — `CONTINUE` means the move fit the map, anything else didn't — and returns a tally plus an `address` note naming the mismatch (requested vs. what the map actually offered, `state.possible_transitions`/`bridge_options` at that moment). None of this blocks, corrects, retries, or prevents anything. It is a durable copy of a verdict the engine already computes and would otherwise discard on the next call — same discard-by-design as `MoveTrace` — nothing more.

**Why this is the default**: same root cause as `ADV-01`/`ADV-02`/`ADV-06` — `dev_mcp` has no visibility into what's actually being built on top of `fpf_thinking_map`. A drift entry cannot distinguish "the model made a mistake" from "the map is missing a transition this legitimate task genuinely needed" — those look identical from inside the ledger, and only someone who knows the domain the map is deployed into can tell them apart. Shipping compliance mode as an enforcement layer instead of a witness would mean guessing that distinction on every integrator's behalf, for deployments this repo has no way to know anything about — could be an e-commerce checkout flow, could be something safety-critical, could be a context nobody here has ever seen or would recognize as risky. There is no version of a default-on hard rail that is correct for all of those at once, and shipping one anyway means being wrong for someone, silently, with no way for `dev_mcp` to know it happened.

There's a second cost, not just a coverage gap: a map that hard-blocks without domain grounding stops being a map and starts being a cage. `traversal.py` frames `step()` as "the LLM's guided reasoning loop" on purpose — the design bet is that the model finds the slice useful, not that it's trapped by it. A model that experiences a cage learns to route around it, which manufactures exactly the silent, adversarial drift this tool exists to surface — worse than the original problem, and harder to see, because now it's evasion instead of an honest miss.

**How to close the gap**: this is a per-deployment decision, not a library feature to request — the same shape as `ADV-08`'s answer, pointed at a different question. Run compliance mode against your own real scenarios, read `drift_entries` and `get_compliance_log()` over actual traffic, and decide — with knowledge of your own domain, your own risk tolerance, and what a wrong move there actually costs — whether a specific, repeated drift is worth hardening into a real rail. If it is, build it the way `ADV-01`/`ADV-02`/`ADV-06` already describe: a `GatePrimitive`/`GateCheck` or a `LogicLayer` rule scoped to that exact transition, driving a hard `BLOCK`/`ABSTAIN` instead of leaving it advisory. `dev_mcp` can hand you the evidence that a rail might be warranted. It cannot tell you where the cage should go, or whether your context calls for one at all — that inspection has to happen on your side, against your own model and your own domain, not fpf's.

---

*v1 — 2026-07-08 (ADV-01/02), v2 — 2026-07-08 (ADV-03..06), v3 — 2026-07-08 (ADV-07), v4 — 2026-07-18 (ADV-08), v5 — 2026-07-18 (ADV-09). All found by actually running scenarios through `dev_mcp` (`scope="core"`) or reading the shipped source directly, not by inspection or guesswork — ADV-09 found while building and testing `dev_mcp`'s own compliance-mode tooling in the same session it shipped in. More advisories get added here the same way — dug up, not invented.*
