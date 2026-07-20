"""Structural detectors for 10 of the 11 documented integrator advisories (docs/deep/ADVISORIES.md).
ADV-09 has no detector — it's about compliance mode itself, not an ActiveState property.

Not a fix. Not enforcement. Nothing here changes engine behavior or blocks
a scenario. This is awareness persistence: when a scenario run's objects
happen to sit in the exact structural situation an advisory describes, say
so — so a tester (human or LLM) sees "you're standing in ADV-03's blind
spot right now" instead of independently rediscovering the same sharp edge
every session, or missing it because nothing pointed at it.

Two tiers, and the distinction matters — don't read every hit as a bug:

- "anomaly": the scenario's own objects show the specific mismatch the
  advisory describes (e.g. EXPIRED evidence still counted present). This
  is a fact about what happened, not a guess.
- "structural-fact" / "heuristic-prompt": the scenario is in a situation
  where the advisory's default behavior applies (e.g. risk_level is
  elevated) — this fires whenever the precondition holds, by design of
  the shipped engine, not because something went wrong. It is a reminder
  to go check, not a discovered anomaly.

Each detector's docstring cites the exact ADVISORIES.md "What" clause it
mirrors. If ADVISORIES.md and this file ever disagree, ADVISORIES.md is
the source of truth — update this file to match, not the other way round.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fpf_thinking_map.primitives import AgencyLevel, Freshness, GateDecision
from fpf_thinking_map.state import ActiveState

try:
    from fpf_thinking_map.logic import LogicLayer
except ImportError:  # pragma: no cover — defensive, logic.py ships with the package
    LogicLayer = None  # type: ignore[assignment,misc]

_KNOWN_RISK_LEVELS = {"low", "normal", "high", "critical"}


@dataclass(frozen=True)
class AdvisoryHit:
    advisory: str
    title: str
    tier: str  # "anomaly" | "structural-fact" | "heuristic-prompt"
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "advisory": self.advisory,
            "title": self.title,
            "tier": self.tier,
            "detail": self.detail,
        }


def _adv01_evidence_staleness(state: ActiveState) -> AdvisoryHit | None:
    """ADV-01 — evidence past TTL (EXPIRED) still satisfies required_evidence; WARN, never BLOCK."""
    for t in state.possible_transitions:
        for eid in t.required_evidence:
            if eid in state.available_evidence_ids and state.effective_freshness(eid) == Freshness.EXPIRED:
                return AdvisoryHit(
                    "ADV-01", "Evidence staleness warns, it does not block", "anomaly",
                    f"transition '{t.transition_id}' required_evidence includes '{eid}', "
                    f"which is EXPIRED but still present in available_evidence_ids — "
                    f"required_evidence alone will not block this move.",
                )
    return None


def _adv02_risk_not_filtering(state: ActiveState) -> AdvisoryHit | None:
    """ADV-02 — possible_transitions is scoped by (context, current_state) only; risk_level never filters it."""
    if state.binding.risk_level in ("high", "critical") and state.possible_transitions:
        return AdvisoryHit(
            "ADV-02", "risk_level doesn't filter transitions on its own", "structural-fact",
            f"risk_level='{state.binding.risk_level}' bound with "
            f"{len(state.possible_transitions)} transition(s) exposed unchanged — "
            f"possible_transitions never reads risk_level. If this domain needs "
            f"risk-based routing, verify a LogicLayer/guard using RiskAbove is actually wired in.",
        )
    return None


def _adv03_context_self_asserted(state: ActiveState) -> AdvisoryHit | None:
    """ADV-03 — active_context_id is plain input; nothing verifies it was reached via cross_bridge().

    Fires on essentially every freshly-built ActiveState with a context bound —
    that IS the documented behavior ("a fresh build_active_state() call has no
    way to know what came before it"), not a detector malfunction. Included so
    the fact stays visible rather than assumed away; read the detail before
    treating a hit as noteworthy on its own.
    """
    ctx_id = state.binding.active_context_id
    if ctx_id and state.trace.bridge_target is None and state.trace.last_transition_id is None:
        return AdvisoryHit(
            "ADV-03", "active_context_id is self-asserted, not verified against how you got there",
            "structural-fact",
            f"active_context_id='{ctx_id}' is set, but this ActiveState's own trace shows "
            f"no cross_bridge()/transition_to() call that reached it — true of every freshly "
            f"constructed binding by design. Only actionable if your harness re-accepts an "
            f"externally-supplied active_context_id later in a session without validating it "
            f"came from this object's own prior cross_bridge() call.",
        )
    return None


def _adv04_contradiction_opt_in(state: ActiveState, logic_layer: "LogicLayer | None") -> AdvisoryHit | None:
    """ADV-04 — consistency_check() only flags contradictions declared via exclusive_with, never inferred."""
    if logic_layer is None or not logic_layer.rules:
        return None
    results = logic_layer.evaluate_all(state)
    satisfied = [r for r in results if r["satisfied"] and r["action"]]
    for i, r1 in enumerate(satisfied):
        for r2 in satisfied[i + 1 :]:
            if r1["action"] == r2["action"]:
                continue
            rule1 = next((r for r in logic_layer.rules if r.name == r1["rule"]), None)
            rule2 = next((r for r in logic_layer.rules if r.name == r2["rule"]), None)
            declared = bool(rule1 and rule2 and (r2["action"] in rule1.exclusive_with or r1["action"] in rule2.exclusive_with))
            if not declared:
                return AdvisoryHit(
                    "ADV-04", "Contradiction detection is opt-in, not inferred from action names",
                    "heuristic-prompt",
                    f"rules '{r1['rule']}' (action='{r1['action']}') and '{r2['rule']}' "
                    f"(action='{r2['action']}') are both satisfied with different actions and "
                    f"neither declares exclusive_with the other — if these actions are meant to "
                    f"be mutually exclusive in this domain, consistency_check() will not catch it "
                    f"without an explicit exclusive_with declaration.",
                )
    return None


def _adv05_degrade_granularity(state: ActiveState) -> AdvisoryHit | None:
    """ADV-05 — gate DEGRADE only fires from a single GateCheck's own partial evidence, never aggregated."""
    for gate in state.semantic_map.gates.values():
        single_item_checks = [c for c in gate.checks if len(c.required_evidence) == 1]
        if len(single_item_checks) < 2:
            continue
        decisions = {c.check_id: c.evaluate(state.available_evidence_ids) for c in single_item_checks}
        has_pass = GateDecision.PASS in decisions.values()
        has_abstain = GateDecision.ABSTAIN in decisions.values()
        if has_pass and has_abstain:
            aggregate = gate.evaluate(state.available_evidence_ids)
            return AdvisoryHit(
                "ADV-05", "Gate DEGRADE only distinguishes partial evidence within a single GateCheck",
                "anomaly",
                f"gate '{gate.gate_id}' has {len(single_item_checks)} single-evidence checks with "
                f"a mix of PASS/ABSTAIN ({decisions}) — genuinely partial completion, but the gate "
                f"aggregate resolves to '{aggregate.value}', indistinguishable from every check "
                f"being ABSTAIN. Group related evidence into one GateCheck if DEGRADE visibility matters here.",
            )
    return None


def _adv06_agency_not_enforced(state: ActiveState) -> AdvisoryHit | None:
    """ADV-06 — agency_level is descriptive metadata surfaced to the model; nothing gates on it by default."""
    passive_roles = [r for r in state.active_roles if r.agency_level == AgencyLevel.PASSIVE]
    if passive_roles and state.possible_transitions:
        return AdvisoryHit(
            "ADV-06", "agency_level is descriptive metadata, not an enforced permission", "structural-fact",
            f"role(s) {[r.role_id for r in passive_roles]} bound as PASSIVE, with "
            f"{len(state.possible_transitions)} transition(s) still exposed identically to a "
            f"DELIBERATIVE-bound role — agency_level gates nothing by default in this engine.",
        )
    return None


def _adv07_risk_case_sensitivity(state: ActiveState) -> AdvisoryHit | None:
    """ADV-07 — RiskAbove does a raw dict lookup; any unrecognized string (including wrong case) silently → 'normal'."""
    rl = state.binding.risk_level
    if rl not in _KNOWN_RISK_LEVELS:
        return AdvisoryHit(
            "ADV-07", "RiskAbove's string matching is case-sensitive and fails silently", "anomaly",
            f"risk_level={rl!r} is not one of {sorted(_KNOWN_RISK_LEVELS)} — RiskAbove will "
            f"silently resolve this to the same numeric level as 'normal' (1), with no error "
            f"and no distinguishing signal in consistency_check() output.",
        )
    return None


def _adv08_no_persistence_surface(state: ActiveState) -> AdvisoryHit | None:
    """ADV-08 — ActiveState/RuntimeBinding/MoveTrace have no serialization surface; #28's backing store is init=False."""
    return AdvisoryHit(
        "ADV-08", "No persistence surface: session continuity is a harness responsibility", "structural-fact",
        f"this ActiveState (current_state={state.current_state!r}, visit_count={state.visit_count}) "
        f"has no to_dict/from_dict — if your harness persists it across an idle period, LLM-side "
        f"context compaction, or a process restart, the stagnation counter's backing store "
        f"(_evidence_added_at/_state_visits/_state_visit_evidence) resets to zero unless you "
        f"restore those private fields yourself, outside the constructor.",
    )


_DESTRUCTIVE_KEYWORDS = frozenset({
    "delete", "drop", "remove", "destroy", "nuke", "wipe", "purge",
    "truncate", "terminate", "revoke", "kill",
})


def _adv10_ungated_destructive_transition(state: ActiveState) -> AdvisoryHit | None:
    """ADV-10 — requires_human_authorization defaults to False (ungated); nothing
    checks whether a transition's own label/id suggests it should have been True.

    Keyword match only, not semantic understanding — same shape as ADV-07's
    string matching, same honesty about it: false positives (an "archive"
    transition that happens to say "remove old copies" in its label) and
    false negatives (a genuinely destructive transition with no alarming
    word in its name) are both expected. This is a heuristic-prompt, not an
    anomaly — it fires on what the map's own labels say, not on proof that
    anything is actually wrong.
    """
    hits: list[tuple[str, list[str]]] = []
    for t in state.semantic_map.transitions.values():
        if t.requires_human_authorization:
            continue
        haystack = f"{t.transition_id} {t.label}".lower()
        matched = sorted(k for k in _DESTRUCTIVE_KEYWORDS if k in haystack)
        if matched:
            hits.append((t.transition_id, matched))
    if not hits:
        return None
    named = ", ".join(f"{tid} ({'/'.join(kw)})" for tid, kw in hits)
    return AdvisoryHit(
        "ADV-10", "Destructive-sounding transition with no requires_human_authorization gate", "heuristic-prompt",
        f"requires_human_authorization defaults to False (ungated) — nothing else in this engine "
        f"checks whether a transition's own name suggests it should have been True. Keyword match "
        f"only ({sorted(_DESTRUCTIVE_KEYWORDS)}), not semantic understanding: false positives and "
        f"false negatives both expected. Transitions in this map with a destructive-sounding "
        f"label/id but no gate set: {named}. If any of these are genuinely destructive, that's a "
        f"silent gap on the map to fix — this engine cannot catch it for you, only point at it.",
    )


def _adv11_unsound_safe_alternative(state: ActiveState) -> AdvisoryHit | None:
    """ADV-11 — safe_alternatives is declared and unvalidated (like bridges_to
    elsewhere in this codebase): nothing checks that a named alternative
    actually exists, is itself less destructive, or hasn't already been
    denied. This is about the map's own declaration being sound — whether
    the model actually reads and uses a validly-declared alternative is a
    different question entirely, and deliberately not this engine's to
    answer. A model that ignores a clearly surfaced, structurally sound
    alternative is a model-capability problem; no amount of engine-side
    validation compensates for that, and trying to would mean silently
    steering the model's choices instead of informing them — the same
    boundary ADV-09 draws around compliance mode.
    """
    unsound: list[str] = []
    for t in state.semantic_map.transitions.values():
        if not t.safe_alternatives:
            continue
        for alt_id in t.safe_alternatives:
            alt = state.semantic_map.transitions.get(alt_id)
            if alt is None:
                unsound.append(f"{t.transition_id} -> {alt_id} (no such transition in this map)")
            elif alt.requires_human_authorization:
                unsound.append(
                    f"{t.transition_id} -> {alt_id} (declared 'safe' but itself "
                    f"requires_human_authorization — questionable as an alternative)"
                )
            elif alt_id in state.denied_authorizations:
                unsound.append(
                    f"{t.transition_id} -> {alt_id} (this alternative was itself already "
                    f"denied: {state.denied_authorizations[alt_id]!r})"
                )
    if not unsound:
        return None
    return AdvisoryHit(
        "ADV-11", "safe_alternatives declaration doesn't hold up structurally", "heuristic-prompt",
        f"safe_alternatives is declared and unvalidated, same as bridges_to elsewhere in this "
        f"codebase — nothing checks that a named alternative exists, is itself less destructive, "
        f"or hasn't already been denied. Unsound entries found: {'; '.join(unsound)}. This checks "
        f"the map's own declaration, not whether the model actually reads or chooses to use it — "
        f"that's a model-capability question this engine deliberately doesn't try to answer.",
    )


def detect_advisories(state: ActiveState, logic_layer: "LogicLayer | None" = None) -> list[AdvisoryHit]:
    """Run all 10 structural detectors (ADV-01..08, ADV-10, ADV-11) against one

    ActiveState (+ optional LogicLayer) and return the hits. ADV-09 has no
    detector here — it's about compliance mode itself, not something an
    ActiveState can exhibit.
    """
    hits: list[AdvisoryHit | None] = [
        _adv01_evidence_staleness(state),
        _adv02_risk_not_filtering(state),
        _adv03_context_self_asserted(state),
        _adv04_contradiction_opt_in(state, logic_layer),
        _adv05_degrade_granularity(state),
        _adv06_agency_not_enforced(state),
        _adv07_risk_case_sensitivity(state),
        _adv08_no_persistence_surface(state),
        _adv10_ungated_destructive_transition(state),
        _adv11_unsound_safe_alternative(state),
    ]
    return [h for h in hits if h is not None]


def find_active_states_and_logic(ns: dict[str, Any]) -> list[tuple[str, ActiveState, "LogicLayer | None"]]:
    """Scan a run_scenario exec namespace for ActiveState objects (by variable name, any name).

    Also looks for a ThinkingMapTraversal in the same namespace to pull its
    bound logic_layer for ADV-04, without requiring the scenario to expose
    the LogicLayer under a specific name either.
    """
    logic_layer: "LogicLayer | None" = None
    for value in ns.values():
        traversal_logic = getattr(value, "logic_layer", None)
        if traversal_logic is not None and LogicLayer is not None and isinstance(traversal_logic, LogicLayer):
            logic_layer = traversal_logic
            break

    found: list[tuple[str, ActiveState, "LogicLayer | None"]] = []
    for name, value in ns.items():
        if isinstance(value, ActiveState):
            found.append((name, value, logic_layer))
    return found
