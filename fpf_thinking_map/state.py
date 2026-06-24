"""Runtime variable binding and active state construction.

Step 2-3 of the agentic run:
- Bind inputs to variables (task, actor, goal, evidence, constraints...)
- Construct active state (which context, which roles, what's live, what's possible)

Horizontal design (#1-#7, #14-#15, #22-#24):
- Roles default to bound-only, not all-in-context
- Transitions scoped to context + state
- Evidence gaps computed per-transition, not context-wide
- Slice method returns tiny per-move submap
- Trace keeps only last move, not full history
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
    GatePrimitive,
    EvidencePrimitive,
    TransitionPrimitive,
    PublicationPrimitive,
    GateDecision,
    Freshness,
)


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

    def register_publication(self, p: PublicationPrimitive) -> None:
        self.publications[p.publication_id] = p

    def roles_in_context(self, context_id: str) -> list[RolePrimitive]:
        return [r for r in self.roles.values() if r.context_id == context_id]

    def transitions_for(self, context_id: str, from_state: str) -> list[TransitionPrimitive]:
        """#1: transitions scoped to context AND state — no cross-context leakage."""
        return [
            t for t in self.transitions.values()
            if t.context_id == context_id and t.from_state == from_state
        ]

    def gates_for_transitions(
        self, transitions: list[TransitionPrimitive],
    ) -> list[GatePrimitive]:
        """#2: only gates referenced by these transitions — no ambient scanning."""
        gate_ids = {t.required_gate_id for t in transitions if t.required_gate_id}
        return [self.gates[gid] for gid in gate_ids if gid in self.gates]


@dataclass
class MoveTrace:
    """#24: compressed trace — last move only, no narrative accumulation."""
    previous_state: str | None = None
    last_transition_id: str | None = None
    blockers: list[str] = field(default_factory=list)
    evidence_delta: list[str] = field(default_factory=list)


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

    def transition_to(self, transition_id: str) -> bool:
        """Attempt a state transition. Returns True if successful."""
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return False
        ctx_id = self.binding.active_context_id
        if ctx_id and t.context_id != ctx_id:
            return False
        if t.from_state != self.current_state:
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
        self.trace = MoveTrace(
            previous_state=self.current_state,
            last_transition_id=transition_id,
        )
        self.current_state = t.to_state
        return True

    def add_evidence(self, evidence_id: str) -> None:
        if evidence_id not in self.binding.current_evidence:
            self.binding.current_evidence.append(evidence_id)
            self.trace.evidence_delta.append(evidence_id)

    def slice(self, transition_id: str) -> dict:
        """#5/#22: tiny operational submap for one move.

        This is what the LLM should chew — not the whole board.
        """
        t = self.semantic_map.transitions.get(transition_id)
        if not t:
            return {"error": f"transition '{transition_id}' not found"}

        gate = self.gate_for_transition(transition_id)
        gate_decision = gate.evaluate(self.available_evidence_ids) if gate else None
        missing = self.missing_evidence_for(transition_id)

        return {
            "move": {
                "id": t.transition_id,
                "label": t.label,
                "from": t.from_state,
                "to": t.to_state,
            },
            "gate": {
                "id": gate.gate_id,
                "label": gate.label,
                "decision": gate_decision.value,
                "missing": gate.missing_evidence(self.available_evidence_ids),
            } if gate else None,
            "evidence": {
                "available": sorted(self.available_evidence_ids & set(
                    t.required_evidence + (
                        [eid for c in gate.checks for eid in c.required_evidence]
                        if gate else []
                    )
                )),
                "missing": missing,
            },
            "roles": [
                {"id": r.role_id, "label": r.label}
                for r in self.active_roles
            ],
            "can_fire": len(missing) == 0 and (
                gate_decision != GateDecision.ABSTAIN if gate_decision else True
            ),
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
            "missing_evidence": self.missing_evidence,
            "gate_status": gate_status,
            "possible_transitions": [
                {
                    "id": t.transition_id,
                    "label": t.label,
                    "to_state": t.to_state,
                    "requires_gate": t.required_gate_id,
                    "missing_evidence": self.missing_evidence_for(t.transition_id),
                }
                for t in transitions
            ],
            "risk_level": self.binding.risk_level,
            "available_tools": self.binding.available_tools,
            "audience": self.binding.audience,
            "trace": {
                "previous_state": self.trace.previous_state,
                "last_transition": self.trace.last_transition_id,
                "blockers": self.trace.blockers,
            } if self.trace.previous_state else None,
        }
