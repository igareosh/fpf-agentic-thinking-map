# Adopted — Ignition Lock / Abort to Orbit (2026-07-20)

This document is the humble version of the release notes: what shipped, where it sits in the general map (not just the destructive-action story used to motivate it), why it exists, how it was tested, and — deliberately — no claim about what it becomes next.

## What shipped

- `TransitionPrimitive.requires_human_authorization: bool` — a transition can be fully legal by every FPF-computed measure (evidence fresh, gate satisfied) and still refuse to fire without a caller passing `authorized=True`, enforced at `ActiveState.transition_to()` itself.
- `ActiveState.pending_authorizations: set[str]` — every currently-escalated, unresolved ask. Plural, because a single-value version of this field lost track of one ask the moment a second one came in before the first was resolved — found by adversarial testing, not design review, and fixed the same session.
- `TransitionPrimitive.safe_alternatives: list[str]` and `ActiveState.deny_pending_authorization(transition_id, reason)` — a transition can declare its non-destructive twins, surfaced before an attempt, not just after a refusal. A denial is recorded with a reason, not silently discarded.
- `ADV-10` and `ADV-11` — two new `dev_mcp`-detected advisories: a keyword-heuristic lint for a destructive-sounding transition with no gate set, and a soundness check on `safe_alternatives` declarations (dangling reference, an alternative that's itself gated, one already denied). Both explicitly heuristic, explicitly not enforcement, same as every advisory before them.

## Where this sits in the general map

The motivating case throughout was destructive actions — a delete, a database wipe, a service restart. That case is real and it's what forced the design, but the mechanism underneath it is not about destruction specifically. It is a general distinction the engine didn't have before: **legal and fireable are not the same property.** `required_evidence` and `required_gate_id` answer "is this move structurally sound." `requires_human_authorization` answers a completely different question — "is this caller allowed to be the one who fires it" — and nothing about that second question requires the move to be destructive. A transition could gate on cost (spend above a threshold), on scope (an action affecting more than N records), on reversibility in either direction, or on anything else a map author decides needs a second party's say-so before it executes. Destructive-action gating is the first and most obvious use, not the only one the primitive supports.

Same shape for `safe_alternatives`: it's a declared relationship between two transitions, structurally identical to how `bridges_to` and `incompatible_with` already worked in this codebase before today. Nothing in its implementation assumes "destructive vs. safe" — it assumes "this move and that move are related as alternatives," which is a relationship a map author could use for reasons that have nothing to do with safety at all.

## Why

Three separate reasons converged on the same design, not one:

1. **A structural gap**, found by studying a different implementation of the same underlying idea (`m0n0x41d/haft`'s Transformer Mandate — model-invocation-disabled binding decisions) and asking whether this engine had an equivalent. It didn't.
2. **A failure-mode gap**, raised directly: escalating unconditionally, with no visibility into whether a non-destructive path existed, risks denying something for reasons nobody could see, which is its own kind of silent failure.
3. **A boundary that had to be drawn explicitly and repeatedly**: this library computes and surfaces facts; it does not decide policy, and it does not compensate for a model or a map author who ignores what's surfaced. Every piece of this feature — the advisories, the alternatives, the denial history — exists to make information visible. None of it exists to force a particular outcome. That boundary came up three separate times during the build (whether `authorized=True` should be forceable by the same process the model runs in; whether the engine should auto-pick a safe alternative; whether `ADV-11` should validate a model's judgment about an alternative rather than just the map's declaration) and landed the same way each time: the engine's job stops at "here is what's true," not "here is what you should do."

## How it was tested, and how you can too

Verify() coverage locally proves the code does what the tests say it does. It doesn't prove the tests asked the right questions. What actually surfaced the one real bug in this feature (`pending_authorizations` losing track of a concurrent ask) was deliberately adversarial testing against the live engine through `dev_mcp` — constructing scenarios nobody had written into the suite yet: two destructive escalations at once, `authorized=True` against a hard gate `BLOCK` (confirming it doesn't bypass), a dangling `safe_alternatives` reference, case sensitivity on the `ADV-10` keyword match.

`dev_mcp` ships with this package specifically so this kind of testing isn't a one-time act by the people who built the feature. `run_scenario(code, scope="core", compliance_mode=True)` runs arbitrary Python scenario code with the package's classes pre-imported, tallies every `attempt_transition()`/`attempt_bridge()` call's own fit/drift verdict, and surfaces every advisory that applies to whatever state your scenario builds. If a claim in this document or in the README doesn't hold up against your own adversarial scenario, `dev_mcp` is the tool to confirm or deny it with — not a request to trust this write-up.

## Conclusion

This shipped as a destructive-action safety feature because that was the concrete, motivating case. What it actually is, underneath that case, is a general primitive for "this move needs a second party's authorization before it fires" plus a general primitive for "this move has a declared alternative." Both are narrow, both are explicit, and both were built by three people (an operator, an end user reasoning through edge cases out loud, and the engine's own adversarial test runs) finding gaps in each other's first drafts, not by one pass of design.

We don't know what a map author building on top of this will actually use it for. The destructive-action case is the one we tested hardest because it's the one that's easiest to get wrong loudly. Everything past that — cost gates, scope gates, multi-party approval chains, whatever "team_ops" or "cluster_ops" or someone else's domain map turns out to need — is genuinely open, and this document isn't the place to guess at it. That's exactly what `dev_mcp` and the advisories are for: not a claim that this is finished, a way to keep checking whether it still holds up as it gets used for things we didn't anticipate.

See [ADVISORIES.md](ADVISORIES.md) (`ADV-10`, `ADV-11`) for the specific integrator-facing gaps this feature's own construction surfaced, and the [main README](../../README.md#ignition-lock-abort-to-orbit-hitl-gating-with-a-reroute-on-denial) for the runtime-facing summary.
