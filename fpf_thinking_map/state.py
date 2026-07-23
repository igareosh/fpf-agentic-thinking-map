"""Runtime state — binding, active state, TTL tracking, and per-move slices.

Three layers:
  RuntimeBinding — input variables for one task (actor, evidence, context)
  SemanticMap    — the static board (all registered primitives, indexed)
  ActiveState    — the live state (map + binding + position + step counter)

The slice() method returns a tiny per-move submap: one transition, its gate,
its evidence with freshness/TTL, whether it can fire, and why not if it can't.
The model chews one slice at a time — never the whole board.

Evidence decays: each step() increments the hop counter, and effective_freshness()
computes whether evidence has gone STALE or EXPIRED based on its semantic floor
and FGR trust factors. The model sees TTL countdowns, not static booleans.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fpf_thinking_map.primitives import (
    ContextPrimitive,
    RolePrimitive,
    RoleAssignment,
    WorkPrimitive,
    WorkPlanPrimitive,
    SpeechActPrimitive,
    CommitmentPrimitive,
    DeonticModality,
    GatePrimitive,
    EvidencePrimitive,
    TransitionPrimitive,
    PublicationPrimitive,
    GateDecision,
    Freshness,
)
from fpf_thinking_map.authorization import AuthorizationReceipt, compute_state_fingerprint
from fpf_thinking_map.pending_input import PendingInput, PendingInputStatus
from fpf_thinking_map.move_intent import MoveIntent


@dataclass
class RuntimeBinding:
    """Variables filled by the current input situation.

    These are the slots the LLM fills when a question/task arrives.
    The thinking map is static; bindings make it live.
    """
    task: str = ""
    goal: str = ""
    actor: str = ""
    actor_role_ids: list[str] = field(default_factory=list)
    audience: str = ""
    available_tools: list[str] = field(default_factory=list)
    current_evidence: list[str] = field(default_factory=list)
    risk_level: str = "normal"
    time_horizon: str = ""
    active_context_id: str | None = None
    constraints: list[str] = field(default_factory=list)
    candidate_actions: list[str] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)
    pending_inputs: list[PendingInput] = field(default_factory=list)
    """Declared external dependencies traversal is waiting on — see

    fpf_thinking_map.pending_input. Empty by default: maps that never
    declare one behave exactly as before, no AWAIT ever fires.
    """


@dataclass
class SemanticMap:
    """The compiled FPF thinking map — all loaded primitives.

    This is the "circuit board" before power is applied.
    Static, reusable across runs.
    """
    contexts: dict[str, ContextPrimitive] = field(default_factory=dict)
    roles: dict[str, RolePrimitive] = field(default_factory=dict)
    role_assignments: dict[str, RoleAssignment] = field(default_factory=dict)
    work_records: dict[str, WorkPrimitive] = field(default_factory=dict)
    work_plans: dict[str, WorkPlanPrimitive] = field(default_factory=dict)
    speech_acts: dict[str, SpeechActPrimitive] = field(default_factory=dict)
    commitments: dict[str, CommitmentPrimitive] = field(default_factory=dict)
    gates: dict[str, GatePrimitive] = field(default_factory=dict)
    evidence: dict[str, EvidencePrimitive] = field(default_factory=dict)
    transitions: dict[str, TransitionPrimitive] = field(default_factory=dict)
    publications: dict[str, PublicationPrimitive] = field(default_factory=dict)
    _ctx_transition_idx: dict[str, dict[str, list[TransitionPrimitive]]] | None = field(
        default=None, init=False, repr=False,
    )

    def _ensure_indexes(self) -> None:
        if self._ctx_transition_idx is None:
            idx: dict[str, dict[str, list[TransitionPrimitive]]] = {}
            for t in self.transitions.values():
                ctx = idx.setdefault(t.context_id, {})
                ctx.setdefault(t.from_state, []).append(t)
            self._ctx_transition_idx = idx

    def register_context(self, ctx: ContextPrimitive) -> None:
        self.contexts[ctx.context_id] = ctx

    def register_role(self, role: RolePrimitive) -> None:
        self.roles[role.role_id] = role

    def register_role_assignment(self, ra: RoleAssignment) -> None:
        self.role_assignments[ra.assignment_id] = ra

    def register_work(self, w: WorkPrimitive) -> None:
        self.work_records[w.work_id] = w

    def register_work_plan(self, wp: WorkPlanPrimitive) -> None:
        self.work_plans[wp.plan_id] = wp

    def register_speech_act(self, sa: SpeechActPrimitive) -> None:
        self.speech_acts[sa.act_id] = sa

    def register_commitment(self, c: CommitmentPrimitive) -> None:
        self.commitments[c.commitment_id] = c

    def register_gate(self, g: GatePrimitive) -> None:
        self.gates[g.gate_id] = g

    def register_evidence(self, e: EvidencePrimitive) -> None:
        self.evidence[e.evidence_id] = e

    def register_transition(self, t: TransitionPrimitive) -> None:
        self.transitions[t.transition_id] = t
        self._ctx_transition_idx = None

    def register_publication(self, p: PublicationPrimitive) -> None:
        self.publications[p.publication_id] = p

    def roles_in_context(self, context_id: str) -> list[RolePrimitive]:
        return [r for r in self.roles.values() if r.context_id == context_id]

    def transitions_for(self, context_id: str, from_state: str) -> list[TransitionPrimitive]:
        """#1: transitions scoped to context AND state — no cross-context leakage."""
        self._ensure_indexes()
        assert self._ctx_transition_idx is not None
        return list(self._ctx_transition_idx.get(context_id, {}).get(from_state, []))

    def gates_for_transitions(
        self, transitions: list[TransitionPrimitive],
    ) -> list[GatePrimitive]:
        """#2: only gates referenced by these transitions — no ambient scanning."""
        gate_ids = {t.required_gate_id for t in transitions if t.required_gate_id}
        return [self.gates[gid] for gid in gate_ids if gid in self.gates]

    def bridge_options(self, context_id: str) -> list[dict[str, Any]]:
        """Precomputed bridge targets with available entry states.

        For each bridge from context_id, checks whether the target context
        has any transitions. Returns target info + entry states for the agent.
        """
        self._ensure_indexes()
        assert self._ctx_transition_idx is not None
        ctx = self.contexts.get(context_id)
        if not ctx:
            return []
        options: list[dict[str, Any]] = []
        for bridge in ctx.bridges_to:
            target_id = bridge.target_context_id
            target_states = self._ctx_transition_idx.get(target_id, {})
            if target_states:
                options.append({
                    "target_context": target_id,
                    "translation_loss": bridge.translation_loss,
                    "mapping": bridge.mapping,
                    "substitution_license": bridge.substitution_license,
                    "entry_states": sorted(target_states.keys()),
                })
        return options


@dataclass
class MoveTrace:
    """#24: compressed trace — last move only, no narrative accumulation."""
    previous_state: str | None = None
    last_transition_id: str | None = None
    bridge_target: str | None = None
    blockers: list[str] = field(default_factory=list)
    evidence_delta: list[str] = field(default_factory=list)
    move_id: str | None = None
    parent_move_id: str | None = None
    """Stamped from a MoveIntent when transition_to()/attempt_transition()

    is called with one — see fpf_thinking_map.move_intent. None for a
    bare transition_id call, exactly as before this field existed.
    """


@dataclass
class ActiveState:
    """The live state after binding inputs to the semantic map.

    Step 3 of the agentic run: what is active right now?
    Scoped to the current move, not the whole map.
    """
    semantic_map: SemanticMap
    binding: RuntimeBinding
    current_state: str = "initial"
    trace: MoveTrace = field(default_factory=MoveTrace)
    step_count: int = 0
    stagnation_threshold: int = 3
    pending_authorizations: set[str] = field(default_factory=set)
    """transition_ids of every requires_human_authorization transition that

    has raised ESCALATE and hasn't been resolved since — plural, on purpose:
    an earlier single str|None version silently lost track of an escalation
    the moment a second, different transition also escalated before the
    first was resolved. current_state alone can't tell a resumed harness
    whether a human is mid-decision on any of these or nothing was ever
    attempted (ADV-08's exact gap). A plain constructor field, not
    init=False like the private counters below, so a harness restoring from
    persistence can pass it straight back in. Each transition_id is removed
    only when that same one fires authorized — see transition_to() — or via
    resolve_pending_authorization()/deny_pending_authorization() below.
    """
    consumed_authorizations: set[str] = field(default_factory=set)
    """request_ids of every AuthorizationReceipt already spent by transition_to().

    A receipt is checked against this set (not just its own expiry/fingerprint)
    so the same human decision can't fire twice — replaying a receipt that
    already succeeded once must not succeed again. A constructor field, same
    replay-across-restarts reasoning as pending_authorizations: a harness
    restoring from persistence needs this back too, or a resumed run would
    accept a receipt it already spent in a previous process.
    """
    denied_authorizations: dict[str, str] = field(default_factory=dict)
    """transition_id -> reason, for every requires_human_authorization

    transition a human has explicitly said no to. Same visibility principle
    as pending_authorizations, aimed at the other side of the decision: a
    denial is a recorded fact, not a silent void a re-attempt can wander
    back into unremarked. Does not permanently block a future authorized=True
    — a human can change their mind — it just means the ESCALATE reason on
    any retry names what was said before.
    """
    _evidence_added_at: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _state_visits: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _state_visit_evidence: dict[str, frozenset[str]] = field(default_factory=dict, init=False, repr=False)
    _authorization_clock: int = field(default=0, init=False, repr=False)
    """Ticks on every step() call AND every successful transition_to() fire —

    AuthorizationReceipt.issued_at_step/expires_at_step are stamped and
    checked against this, not step_count. step_count only advances via
    step() and specifically drives evidence TTL decay (see step()'s own
    docstring); it does not advance when a transition actually fires via
    transition_to()/attempt_transition() without an intervening step()
    call. Binding receipt expiry to step_count left a real gap: issue a
    receipt against fingerprint F, fire once (consuming it), fire an
    unrelated transition back to fingerprint F with zero step() calls in
    between, and a second, different receipt issued earlier against F
    would still validate — the fingerprint matches again and step_count
    never moved to expire it. Found via adversarial testing against
    attempt_transition()-only workflows (2026-07-23) — see
    check_authorization_receipt's round-trip case. Deliberately not fixed
    by making transition_to() bump step_count itself: that would also
    accelerate evidence TTL decay on every fire, a much bigger and
    unrelated semantic change to what step_count means.
    """

    def __post_init__(self) -> None:
        for eid in self.binding.current_evidence:
            if eid not in self._evidence_added_at:
                self._evidence_added_at[eid] = 0

    @property
    def active_context(self) -> ContextPrimitive | None:
        if self.binding.active_context_id:
            return self.semantic_map.contexts.get(self.binding.active_context_id)
        return None

    @property
    def active_assignments(self) -> list[RoleAssignment]:
        """R07/R08: role assignments for the current actor in the active context.

        If assignments exist on the map, use them. Otherwise fall through
        to actor_role_ids for backward compatibility.
        """
        if not self.semantic_map.role_assignments:
            return []
        ctx_id = self.binding.active_context_id
        actor = self.binding.actor
        return [
            ra for ra in self.semantic_map.role_assignments.values()
            if ra.holder_id == actor
            and (not ctx_id or ra.context_id == ctx_id)
            and not ra.expired
        ]

    @property
    def active_roles(self) -> list[RolePrimitive]:
        """Roles resolved from assignments (if available) or direct binding."""
        assignments = self.active_assignments
        if assignments:
            ctx_id = self.binding.active_context_id
            return [
                self.semantic_map.roles[ra.role_id]
                for ra in assignments
                if ra.role_id in self.semantic_map.roles
                and (not ctx_id or self.semantic_map.roles[ra.role_id].context_id == ctx_id)
            ]
        if not self.binding.actor_role_ids:
            return []
        ctx_id = self.binding.active_context_id
        return [
            self.semantic_map.roles[rid]
            for rid in self.binding.actor_role_ids
            if rid in self.semantic_map.roles
            and (not ctx_id or self.semantic_map.roles[rid].context_id == ctx_id)
        ]

    @property
    def available_evidence_ids(self) -> set[str]:
        return set(self.binding.current_evidence)

    @property
    def unresolved_pending_inputs(self) -> list[PendingInput]:
        """PendingInputs still EXPECTED or PENDING — what AWAIT is checking for.

        RECEIVED/FAILED/CANCELLED entries stay in binding.pending_inputs as
        a record (an adapter-owned decision, not the core's to prune) but
        drop out of this view, since they no longer block anything.
        """
        return [pi for pi in self.binding.pending_inputs if pi.unresolved]

    def effective_freshness(self, evidence_id: str) -> Freshness:
        """Compute freshness factoring in TTL decay over traversal steps.

        Uses computed_ttl which resolves: explicit ttl_steps > floor+FGR > None.
        Static freshness is the floor. TTL can only degrade, never improve.
        age >= ttl → STALE, age >= 2×ttl → EXPIRED.
        """
        ev = self.semantic_map.evidence.get(evidence_id)
        if not ev:
            return Freshness.UNKNOWN
        ttl = ev.computed_ttl
        if ttl is not None and evidence_id in self._evidence_added_at:
            age = self.step_count - self._evidence_added_at[evidence_id]
            if age >= ttl * 2:
                return Freshness.EXPIRED
            if age >= ttl:
                if ev.freshness == Freshness.EXPIRED:
                    return Freshness.EXPIRED
                return Freshness.STALE
        return ev.freshness

    def ttl_remaining(self, evidence_id: str) -> int | None:
        """Steps until this evidence goes STALE. None if no TTL applies."""
        ev = self.semantic_map.evidence.get(evidence_id)
        if not ev:
            return None
        ttl = ev.computed_ttl
        if ttl is None:
            return None
        added_at = self._evidence_added_at.get(evidence_id, 0)
        return max(0, ttl - (self.step_count - added_at))

    def _visit_key(self) -> str:
        return f"{self.binding.active_context_id}:{self.current_state}"

    def register_visit(self) -> int:
        """#28: count consecutive step()s at this (context, state) pair.

        A revisit with the same evidence set is not progress — it's the
        countable, deterministic version of "the agent is stuck," instead
        of asking the model to introspect about its own psychology. New
        evidence resets the counter: different evidence means there's
        something new to try, not a loop.

        Called once per step() — see traversal.py. Returns the new count.

        Syntactic, not semantic: this tracks set membership on evidence_ids,
        not whether anything meaningful actually happened. Two consequences
        a caller should know about. (1) A harness that adds a new evidence_id
        on every attempt — even a low-value one — resets the counter every
        time and this will never fire, no matter how unproductive the loop
        actually is. (2) This only sees what reaches step(); flailing that
        happens inside a single turn and never gets reported back as a step()
        call is invisible to it. The guarantee this method gives is
        conditional: if one real attempt maps to one step() call, and
        evidence is only added when it's genuinely new, revisits are bounded
        at stagnation_threshold. It cannot judge whether an attempt was real
        progress — that's a semantic question this library doesn't answer.
        """
        key = self._visit_key()
        snapshot = frozenset(self.available_evidence_ids)
        if self._state_visit_evidence.get(key) != snapshot:
            self._state_visits[key] = 0
            self._state_visit_evidence[key] = snapshot
        self._state_visits[key] = self._state_visits.get(key, 0) + 1
        return self._state_visits[key]

    @property
    def visit_count(self) -> int:
        """How many consecutive step()s have landed on this (context, state)
        with the current evidence set, without advancing."""
        return self._state_visits.get(self._visit_key(), 0)

    @property
    def visits_remaining(self) -> int:
        """Countdown to stagnation_threshold — mirrors ttl_remaining's shape."""
        return max(0, self.stagnation_threshold - self.visit_count)

    @property
    def is_stagnant(self) -> bool:
        return self.visit_count >= self.stagnation_threshold

    @property
    def possible_transitions(self) -> list[TransitionPrimitive]:
        """#1: scoped to active context + current state."""
        ctx_id = self.binding.active_context_id or ""
        return self.semantic_map.transitions_for(ctx_id, self.current_state)

    def gate_for_transition(self, transition_id: str) -> GatePrimitive | None:
        """#2: get the single gate for a specific transition."""
        t = self.semantic_map.transitions.get(transition_id)
        if not t or not t.required_gate_id:
            return None
        return self.semantic_map.gates.get(t.required_gate_id)

    def missing_evidence_for(self, transition_id: str) -> list[str]:
        """#3/#7: per-transition evidence + readiness check."""
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return []
        needed: set[str] = set(t.required_evidence)
        needed.update(t.readiness_refs)
        if t.required_gate_id:
            gate = self.semantic_map.gates.get(t.required_gate_id)
            if gate:
                needed.update(
                    eid for check in gate.checks for eid in check.required_evidence
                )
        return sorted(needed - self.available_evidence_ids)

    @property
    def missing_evidence(self) -> list[str]:
        """Aggregate missing evidence across current transitions only."""
        missing: set[str] = set()
        for t in self.possible_transitions:
            missing.update(self.missing_evidence_for(t.transition_id))
        return sorted(missing)

    def verify_authorization(
        self, transition_id: str, receipt: AuthorizationReceipt
    ) -> tuple[bool, str]:
        """Check a receipt against *this* state, right now — not against
        whatever state existed when it was issued.

        Every failure names itself, so an ESCALATE built on top of this can
        say something more actionable than "not authorized":
          - wrong transition: receipt was issued for a different move
          - already consumed: same request_id spent once already — replay
          - expired: the authorization clock has advanced past what the
            receipt allows — see _authorization_clock's own docstring for
            why this is a dedicated counter, not step_count
          - stale state: current_state/context/evidence moved since the
            human looked — the exact TOCTOU this exists to catch
        """
        if receipt.transition_id != transition_id:
            return False, (
                f"receipt issued for '{receipt.transition_id}', "
                f"attempted transition is '{transition_id}'"
            )
        if receipt.request_id in self.consumed_authorizations:
            return False, f"receipt '{receipt.request_id}' already consumed"
        if self._authorization_clock > receipt.expires_at_step:
            return False, (
                f"receipt expired at step {receipt.expires_at_step}, "
                f"current step is {self._authorization_clock}"
            )
        current_fingerprint = compute_state_fingerprint(self)
        if receipt.state_fingerprint != current_fingerprint:
            return False, (
                "state has changed since this receipt was issued — issued "
                f"against {receipt.state_fingerprint}, current is {current_fingerprint}"
            )
        return True, "ok"

    def transition_to(
        self,
        transition_id: str,
        authorized: bool = False,
        authorization: AuthorizationReceipt | None = None,
        intent: MoveIntent | None = None,
    ) -> bool:
        """Attempt a state transition. Returns True if successful.

        requires_human_authorization transitions refuse to fire without
        authorized=True or a verified `authorization` receipt, even if
        evidence and gates are fully satisfied — this is the one check
        that isn't about state, it's about who is allowed to pull the
        trigger. Checked here, not just in the Outcome-returning wrapper,
        so calling this method directly can't bypass it.

        `authorization`, when given, is independently re-verified here
        (not trusted from the caller) — same reasoning as authorized=:
        a bad receipt must not fire just because some earlier check passed.

        `intent`, when given, only stamps `trace.move_id`/`parent_move_id`
        on success — it carries no legality weight. A MoveIntent for a
        transition that isn't this one, or whose parameters wouldn't
        satisfy a gate, doesn't change whether this call fires; that's
        deliberate — see fpf_thinking_map.move_intent.
        """
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return False
        ctx_id = self.binding.active_context_id
        if ctx_id and t.context_id != ctx_id:
            return False
        if t.from_state != self.current_state:
            return False
        if authorization is not None:
            ok, _ = self.verify_authorization(transition_id, authorization)
            if not ok:
                return False
            authorized = True
        if t.requires_human_authorization and not authorized:
            return False
        if t.required_evidence:
            if set(t.required_evidence) - self.available_evidence_ids:
                return False
        if t.readiness_refs:
            if set(t.readiness_refs) - self.available_evidence_ids:
                return False
        if t.required_gate_id:
            gate = self.semantic_map.gates.get(t.required_gate_id)
            decision = gate.evaluate(self.available_evidence_ids)
            if decision in (GateDecision.ABSTAIN, GateDecision.BLOCK):
                return False
        # An intent naming some other transition_id isn't this move's record —
        # stamping it anyway would corrupt trace with an unrelated move's
        # identity. Treated as if no intent were given, not an error: intent
        # carries no legality weight, so a mismatch doesn't block the fire
        # either, it just isn't credited.
        matching_intent = intent if intent and intent.transition_id == transition_id else None
        self.trace = MoveTrace(
            previous_state=self.current_state,
            last_transition_id=transition_id,
            move_id=matching_intent.move_id if matching_intent else None,
            parent_move_id=matching_intent.parent_move_id if matching_intent else None,
        )
        self.current_state = t.to_state
        # every actual fire is a real change in the world, whether or not a
        # step() call happened first — a receipt issued against the state
        # before this fire must not survive it indefinitely just because
        # nobody called step() in between. See _authorization_clock's
        # docstring for the gap this closes.
        self._authorization_clock += 1
        if authorization is not None:
            self.consumed_authorizations.add(authorization.request_id)
        # this specific ask got resolved (approved and fired) — remove it.
        # Firing some *other* transition must not remove it: that would
        # silently lose track of a still-unanswered human ask just
        # because unrelated work happened to move forward. discard(), not
        # remove(): firing a transition that was never pending is normal,
        # not an error.
        self.pending_authorizations.discard(transition_id)
        return True

    def resolve_pending_authorization(self, transition_id: str) -> None:
        """Clear one pending ask without firing it, and without a trace.

        For a harness deciding this specific ask is stale or no longer
        relevant — the traversal moved past the question entirely, not "no."
        If a human actually said no, use deny_pending_authorization()
        instead: that one remembers why, this one doesn't.
        """
        self.pending_authorizations.discard(transition_id)

    def deny_pending_authorization(self, transition_id: str, reason: str = "") -> None:
        """A human said no. Records it — a denial is a fact, not a void.

        Removes transition_id from pending_authorizations if it was there.
        Does not block a later authorized=True on the same transition_id —
        a human can change their mind — but any retry's ESCALATE reason will
        name this denial, so it isn't silently re-asked as if fresh. Pair
        with TransitionPrimitive.safe_alternatives on the denied transition
        to know what else was declared as its non-destructive twin; this
        method doesn't pick one, it only makes sure the denial is visible.
        """
        self.denied_authorizations[transition_id] = reason
        self.pending_authorizations.discard(transition_id)

    def cross_bridge(self, target_context_id: str, entry_state: str) -> tuple[bool, str]:
        """#26: validated writeback for a cross-context bridge crossing.

        FPF A.6.9 gives bridges an explicit fidelity contract — substitution_license
        and translation_loss — but until now that contract was surfaced only as
        advisory metadata in bridge_options(); nothing enforced it before the LLM
        wandered into the target context. This closes that gap: the engine, not
        the model, decides whether a crossing is licensed.

        An unlicensed bridge (substitution_license=False) is fine for low/normal
        risk moves — the translation_loss is real but tolerable. At high/critical
        risk_level it is refused: a lossy, unlicensed substitution must not carry
        weight it wasn't licensed for.

        Returns (ok, reason). On ok=True, current_state and active_context_id are
        updated and the crossing is recorded in trace as bridge_target.
        """
        ctx = self.active_context
        if not ctx:
            return False, "no active context to bridge from"

        bridge = next(
            (b for b in ctx.bridges_to if b.target_context_id == target_context_id),
            None,
        )
        if bridge is None:
            return False, f"no bridge from '{ctx.context_id}' to '{target_context_id}'"

        if not self.semantic_map.transitions_for(target_context_id, entry_state):
            return False, (
                f"'{entry_state}' is not a valid entry state in '{target_context_id}' "
                f"(no transitions start there)"
            )

        if not bridge.substitution_license and self.binding.risk_level in ("high", "critical"):
            return False, (
                f"bridge to '{target_context_id}' is unlicensed for substitution "
                f"(translation_loss: '{bridge.translation_loss}') — risk_level "
                f"'{self.binding.risk_level}' requires a licensed bridge"
            )

        self.trace = MoveTrace(
            previous_state=self.current_state,
            bridge_target=target_context_id,
        )
        self.binding.active_context_id = target_context_id
        self.current_state = entry_state
        return True, f"crossed to '{target_context_id}' at '{entry_state}'"

    def add_evidence(self, evidence_id: str) -> None:
        if evidence_id not in self.binding.current_evidence:
            self.binding.current_evidence.append(evidence_id)
            self.trace.evidence_delta.append(evidence_id)
        if evidence_id not in self._evidence_added_at:
            self._evidence_added_at[evidence_id] = self.step_count

    def response_contract(self, transition_id: str | None = None) -> dict:
        """Output contract — what the model's response must contain.

        Pre-filled fields come from the computed state (basis, scope,
        modality, canonical terms, constraints). Empty fields are for the
        model to fill (claim, risky aliases). This is why the code exists:
        so these fields have precomputed, TTL-checked, guard-validated values
        instead of being re-derived by the model from scratch each step.
        """
        ctx = self.active_context
        ctx_id = self.binding.active_context_id

        if transition_id:
            t = self.semantic_map.transitions.get(transition_id)
            relevant = set(t.required_evidence) if t else set()
            basis = [
                {"id": eid, "freshness": self.effective_freshness(eid).value,
                 "ttl_remaining": self.ttl_remaining(eid)}
                for eid in sorted(relevant & self.available_evidence_ids)
            ]
        else:
            basis = [
                {"id": eid, "freshness": self.effective_freshness(eid).value,
                 "ttl_remaining": self.ttl_remaining(eid)}
                for eid in sorted(self.available_evidence_ids)
            ]

        commitments = [
            c for c in self.semantic_map.commitments.values()
            if not ctx_id or c.context_id == ctx_id
        ]

        return {
            "claim": "",
            "scope": ctx.label if ctx else "",
            "basis": basis,
            "allowed_use": [
                c.scope for c in commitments
                if c.modality in (DeonticModality.MUST, DeonticModality.SHOULD)
                and c.scope
            ],
            "not_allowed_use": [
                c.scope for c in commitments
                if c.modality in (DeonticModality.MUST_NOT, DeonticModality.SHOULD_NOT)
                and c.scope
            ] + (ctx.invariants if ctx else []),
            "obligations": [
                {"commitment": c.label, "force": c.modality.value, "scope": c.scope}
                for c in commitments
            ],
            "audience": self.binding.audience,
            "correct_terms": ctx.glossary if ctx else {},
            "risky_aliases": [],
        }

    def slice(
        self,
        transition_id: str,
        guard_blockers: list[str] | None = None,
    ) -> dict:
        """#5/#22: tiny operational submap for one move.

        This is what the LLM should chew — not the whole board.
        Includes blockers for HITL visibility when can_fire is False.
        """
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return {"error": f"transition '{transition_id}' not found"}

        gate = self.gate_for_transition(transition_id)
        gate_decision = gate.evaluate(self.available_evidence_ids) if gate else None
        missing = self.missing_evidence_for(transition_id)

        blockers: list[str] = []
        if missing:
            blockers.append(f"missing evidence: {missing}")
        if gate and gate_decision == GateDecision.ABSTAIN:
            blockers.append(
                f"gate '{gate.gate_id}' abstains — insufficient evidence: "
                f"{gate.missing_evidence(self.available_evidence_ids)}"
            )
        if gate and gate_decision == GateDecision.BLOCK:
            blockers.append(f"gate '{gate.gate_id}' blocks — hard denial")
        if guard_blockers:
            blockers.extend(guard_blockers)

        can_fire = len(missing) == 0 and (
            gate_decision not in (GateDecision.ABSTAIN, GateDecision.BLOCK)
            if gate_decision else True
        ) and not t.requires_human_authorization
        if t.requires_human_authorization and not blockers:
            blockers.append("requires_human_authorization — requires human authorization, not model-invoked")

        relevant_eids = sorted(self.available_evidence_ids & set(
            t.required_evidence + (
                [eid for c in gate.checks for eid in c.required_evidence]
                if gate else []
            )
        ))

        return {
            "move": {
                "id": t.transition_id,
                "label": t.label,
                "from": t.from_state,
                "to": t.to_state,
                "requires_human_authorization": t.requires_human_authorization,
                "safe_alternatives": t.safe_alternatives,
                "previously_denied": self.denied_authorizations.get(t.transition_id),
                "currently_pending": t.transition_id in self.pending_authorizations,
            },
            "gate": {
                "id": gate.gate_id,
                "label": gate.label,
                "decision": gate_decision.value,
                "missing": gate.missing_evidence(self.available_evidence_ids),
            } if gate else None,
            "evidence": {
                "available": [
                    {
                        "id": eid,
                        "freshness": self.effective_freshness(eid).value,
                        "ttl_remaining": self.ttl_remaining(eid),
                    }
                    for eid in relevant_eids
                ],
                "missing": missing,
            },
            "roles": [
                {"id": r.role_id, "label": r.label}
                for r in self.active_roles
            ],
            "can_fire": can_fire,
            "blockers": blockers,
            "stagnation": {
                "visits": self.visit_count,
                "remaining": self.visits_remaining,
                "threshold": self.stagnation_threshold,
                "is_stagnant": self.is_stagnant,
            },
            "response_contract": self.response_contract(transition_id),
        }

    def to_llm_prompt_state(self) -> dict:
        """Export the active state as a dict the LLM reasons over.

        Scoped to current transitions only — not the whole map.
        """
        ctx = self.active_context
        transitions = self.possible_transitions

        relevant_gates = self.semantic_map.gates_for_transitions(transitions)
        gate_status = {
            g.gate_id: g.evaluate(self.available_evidence_ids).value
            for g in relevant_gates
        }

        return {
            "active_context": ctx.context_id if ctx else None,
            "active_context_label": ctx.label if ctx else None,
            "active_roles": [
                {"role_id": r.role_id, "label": r.label, "agency": r.agency_level.value}
                for r in self.active_roles
            ],
            "goal": self.binding.goal,
            "task": self.binding.task,
            "current_state": self.current_state,
            "candidate_actions": self.binding.candidate_actions,
            "constraints": self.binding.constraints,
            "available_evidence": sorted(self.available_evidence_ids),
            "evidence_status": {
                eid: {
                    "freshness": self.effective_freshness(eid).value,
                    "ttl_remaining": self.ttl_remaining(eid),
                }
                for eid in sorted(self.available_evidence_ids)
            },
            "missing_evidence": self.missing_evidence,
            "gate_status": gate_status,
            "possible_transitions": [
                {
                    "id": t.transition_id,
                    "label": t.label,
                    "to_state": t.to_state,
                    "requires_gate": t.required_gate_id,
                    "missing_evidence": self.missing_evidence_for(t.transition_id),
                    "requires_human_authorization": t.requires_human_authorization,
                    "safe_alternatives": t.safe_alternatives,
                }
                for t in transitions
            ],
            "risk_level": self.binding.risk_level,
            "available_tools": self.binding.available_tools,
            "audience": self.binding.audience,
            "step_count": self.step_count,
            "stagnation": {
                "visits": self.visit_count,
                "remaining": self.visits_remaining,
                "threshold": self.stagnation_threshold,
                "is_stagnant": self.is_stagnant,
            },
            "trace": {
                "previous_state": self.trace.previous_state,
                "last_transition": self.trace.last_transition_id,
                "blockers": self.trace.blockers,
            } if self.trace.previous_state else None,
            "pending_authorizations": sorted(self.pending_authorizations),
            "pending_inputs": [
                {
                    "id": pi.input_id,
                    "label": pi.label,
                    "status": pi.status.value,
                    "expected_evidence": pi.expected_evidence_ids,
                    "wake_conditions": pi.wake_conditions,
                }
                for pi in sorted(self.unresolved_pending_inputs, key=lambda p: p.input_id)
            ],
        }
