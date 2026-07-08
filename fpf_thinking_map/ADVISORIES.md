# Advisories for integrators

Not defects. These are places where `fpf_thinking_map` deliberately stays minimal and leaves a real decision to whoever builds a domain map on top of it — `scope="user-extension"` territory, not something the publisher will fold into the core, because building it in would mean guessing your domain's actual requirement instead of you stating it explicitly.

Each advisory: what the default behavior actually is, why that's the default, and exactly how to get stricter behavior if your domain needs it.

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

*v1 — 2026-07-08 (ADV-01/02), v2 — 2026-07-08 (ADV-03..06). All found by actually running scenarios through `dev_mcp` (`scope="core"`), not by inspection or guesswork. More advisories get added here the same way — dug up, not invented.*
