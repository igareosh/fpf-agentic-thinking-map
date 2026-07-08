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

*v1 — 2026-07-08. Both found by actually running scenarios through `dev_mcp` (`scope="core"`), not by inspection or guesswork. More advisories get added here the same way — dug up, not invented.*
