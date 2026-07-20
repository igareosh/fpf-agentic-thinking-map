"""Compliance Mode Inspector — durable record of map fit/drift, nothing more.

The engine already computes whether a committed move fits the map: every
`attempt_transition()` / `attempt_bridge()` call returns Outcome.kind, and
that kind is CONTINUE exactly when the move was accepted. Normally the
caller reads that once and it's gone (same discard-by-design as
MoveTrace's "last move only, no narrative accumulation").

This module does one thing: wraps those two calls so the verdict survives,
and tallies it. It does not ask why a move didn't fit — it can't, since
that depends on model internals nobody here has access to. It only
records two facts side by side: what the map actually had on offer at
that moment (`expected` — state.possible_transitions / bridge_options,
values the engine already computes) and what was requested instead. That
pairing is what makes a drift entry fast to scan: no re-deriving "what
should this have been" by hand, it's just sitting right there next to
what happened.

compliance_mode is a plain, explicit run_scenario(..., compliance_mode=True)
keyword — off by default, no hidden state, no env var. See server.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComplianceRecord:
    call: str  # "attempt_transition" | "attempt_bridge"
    requested: str
    expected: list[str]  # what state.possible_transitions / bridge_options offered, pre-call
    from_state: str
    outcome_kind: str
    fit: bool


def _address_note(drifted: list[ComplianceRecord]) -> str:
    """One templated line, built only from recorded fields — no generation, no "why".

    Names the first mismatch directly so the model reading it can act on the spot;
    points at drift_entries for the rest rather than repeating all of them in prose.
    """
    first = drifted[0]
    rest = f" ({len(drifted)} total this run — see drift_entries for the rest.)" if len(drifted) > 1 else ""
    return (
        f"{first.call} requested '{first.requested}' from '{first.from_state}' — "
        f"the map's own offer there was {first.expected}, outcome was '{first.outcome_kind}'. "
        f"Choose from what the map offered, or proceed only if diverging is intended.{rest}"
    )


@dataclass
class ComplianceLedger:
    """Collects records for one run_scenario call. Nothing here interprets anything."""
    records: list[ComplianceRecord] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        total = len(self.records)
        drifted = [r for r in self.records if not r.fit]
        out: dict[str, Any] = {
            "total_attempts": total,
            "fit_map": total - len(drifted),
            "drifted": len(drifted),
            "drift_entries": [
                {
                    "call": r.call,
                    "requested": r.requested,
                    "expected": r.expected,
                    "from_state": r.from_state,
                    "outcome": r.outcome_kind,
                }
                for r in drifted
            ],
        }
        if drifted:
            out["address"] = _address_note(drifted)
        return out


def _safe_expected(fn) -> list[str]:
    """Never let capturing 'what the map offered' break the real call it's watching."""
    try:
        return fn()
    except Exception:  # noqa: BLE001 — witness layer, must not shadow the real outcome
        return []


def wrap_traversal_class(traversal_cls: type, ledger: ComplianceLedger) -> type:
    """Return a subclass of traversal_cls that records attempt_transition/attempt_bridge
    verdicts into `ledger`, then behaves identically to the original.

    Scenario code that does `ThinkingMapTraversal(semantic_map)` never has to know —
    same constructor, same methods, same return values, one extra write per call.
    """

    orig_attempt_transition = traversal_cls.attempt_transition
    orig_attempt_bridge = traversal_cls.attempt_bridge

    class ComplianceTraversal(traversal_cls):  # type: ignore[misc, valid-type]
        def attempt_transition(self, state, transition_id, **kwargs):  # noqa: D102 — thin wrapper, no new behavior
            from_state = state.current_state
            # captured before the call: transition_to() mutates current_state on success,
            # so possible_transitions() must be read against the pre-move state.
            expected = _safe_expected(lambda: [t.transition_id for t in state.possible_transitions])
            outcome = orig_attempt_transition(self, state, transition_id, **kwargs)
            ledger.records.append(
                ComplianceRecord(
                    call="attempt_transition",
                    requested=transition_id,
                    expected=expected,
                    from_state=from_state,
                    outcome_kind=outcome.kind.value,
                    fit=(outcome.kind.value == "continue"),
                )
            )
            return outcome

        def attempt_bridge(self, state, target_context_id, entry_state):  # noqa: D102
            from_state = state.current_state
            ctx_id = state.binding.active_context_id or ""
            expected = _safe_expected(
                lambda: [opt["target_context"] for opt in self.semantic_map.bridge_options(ctx_id)]
            )
            outcome = orig_attempt_bridge(self, state, target_context_id, entry_state)
            ledger.records.append(
                ComplianceRecord(
                    call="attempt_bridge",
                    requested=target_context_id,
                    expected=expected,
                    from_state=from_state,
                    outcome_kind=outcome.kind.value,
                    fit=(outcome.kind.value == "continue"),
                )
            )
            return outcome

    ComplianceTraversal.__name__ = traversal_cls.__name__
    ComplianceTraversal.__qualname__ = traversal_cls.__qualname__
    return ComplianceTraversal
