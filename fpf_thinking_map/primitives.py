"""Compiled FPF semantic primitives.

These are the "circuit board components" — the pre-shaped semantic field
extracted from FPF spec patterns. Each primitive maps to one or more
FPF spec sections and carries the structural semantics the LLM navigates.

Not a 1:1 copy of FPF. A compiled distillation: enough structure to
constrain reasoning, enough openness for the LLM to interpret.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# A.1.1 — U.BoundedContext: The Semantic Frame
# ---------------------------------------------------------------------------

@dataclass
class ContextPrimitive:
    """A bounded semantic frame where meaning is local.

    FPF A.1.1: meaning is defined inside a context. Cross-context use
    requires explicit Bridges with declared translation loss.
    Contexts do not form holarchies — no containment or inheritance.
    Cross-context relation goes through bridges only.
    """
    context_id: str
    label: str
    glossary: dict[str, str] = field(default_factory=dict)
    invariants: list[str] = field(default_factory=list)
    bridges_to: list[ContextBridge] = field(default_factory=list)

    def term_defined(self, term: str) -> bool:
        return term in self.glossary

    def resolve_term(self, term: str) -> str | None:
        return self.glossary.get(term)


@dataclass
class ContextBridge:
    """Explicit bridge between two bounded contexts.

    FPF A.6.9: cross-context sameness must go through bridges
    with direction, substitution license, and loss notes.
    """
    target_context_id: str
    mapping: dict[str, str] = field(default_factory=dict)
    translation_loss: str = ""
    substitution_license: bool = False


# ---------------------------------------------------------------------------
# A.2 — Role Taxonomy + A.2.1 U.RoleAssignment + A.13 Agency Spectrum
# ---------------------------------------------------------------------------

class AgencyLevel(Enum):
    """FPF A.13: agency is a spectrum, not binary."""
    PASSIVE = "passive"
    REACTIVE = "reactive"
    AUTONOMOUS = "autonomous"
    DELIBERATIVE = "deliberative"


@dataclass
class RolePrimitive:
    """A role assignment within a bounded context.

    FPF A.2: Role ≠ Method ≠ Work (A.7 strict distinction).
    A role is an assignment/mask, not an identity. The same holder
    can have multiple roles in different contexts.

    FPF A.2.7: roles have algebra — specialization (≤),
    incompatibility (⊥), bundles (⊗).
    """
    role_id: str
    label: str
    context_id: str
    agency_level: AgencyLevel = AgencyLevel.REACTIVE
    responsibilities: list[str] = field(default_factory=list)
    incompatible_with: list[str] = field(default_factory=list)
    specializes: str | None = None
    required_evidence_roles: list[str] = field(default_factory=list)

    def conflicts_with(self, other_role_id: str) -> bool:
        return other_role_id in self.incompatible_with


# ---------------------------------------------------------------------------
# A.2.1 — U.RoleAssignment: Contextual Role Assignment
# ---------------------------------------------------------------------------

@dataclass
class RoleAssignment:
    """A binding of a holder to a role inside a bounded context.

    FPF A.2.1: assignment is distinct from role definition and from
    role enactment (work done under the assignment).
    The assignment can have a validity window — expired assignments
    should not authorize new work.
    """
    assignment_id: str
    holder_id: str
    role_id: str
    context_id: str
    valid_from: str = ""
    valid_until: str = ""
    expired: bool = False


# ---------------------------------------------------------------------------
# A.15, A.15.1, A.15.2 — Work & WorkPlan
# ---------------------------------------------------------------------------

@dataclass
class WorkPrimitive:
    """A record of occurrence (enactment).

    FPF A.15.1 (U.Work): the record of what actually happened.
    Work is execution/occurrence, distinct from Role, Method, and Plan.
    A plan does NOT constitute having done the work.
    """
    work_id: str
    label: str
    context_id: str
    method_id: str | None = None
    performed_under: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class WorkPlanPrimitive:
    """A schedule of intent — NOT a record of work done.

    FPF A.15.2 (U.WorkPlan): what is intended to happen.
    Distinct type from WorkPrimitive — the type IS the distinction.
    A plan existing does not mean the work was executed.
    """
    plan_id: str
    label: str
    context_id: str
    method_id: str | None = None
    intended_role_id: str | None = None
    planned_evidence: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# A.2.9 — U.SpeechAct: Communicative Work Object
# ---------------------------------------------------------------------------

class SpeechActType(Enum):
    """What the speech act does."""
    APPROVE = "approve"
    AUTHORIZE = "authorize"
    REVOKE = "revoke"
    PUBLISH = "publish"
    REQUEST = "request"


@dataclass
class SpeechActPrimitive:
    """A communicative work occurrence — approval, authorization, revocation.

    FPF A.2.9: a U.Work whose primary effect is communicative.
    The act can institute, update, or revoke commitments, role assignments,
    and statuses by reference.

    Agentic behavior change: "owner_approval" stops being a magic string
    evidence ID. It becomes a speech act with: who approved, when, what it
    institutes, whether it's still valid. Guards can check these.
    """
    act_id: str
    act_type: SpeechActType
    actor_id: str
    context_id: str
    performed_under: str | None = None
    addressed_to: str = ""
    institutes: list[str] = field(default_factory=list)
    revokes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    expired: bool = False


# ---------------------------------------------------------------------------
# A.2.8 — U.Commitment: Deontic Commitment Object
# ---------------------------------------------------------------------------

class DeonticModality(Enum):
    """RFC 2119 / BCP-14 aligned modalities."""
    MUST = "must"
    SHOULD = "should"
    MAY = "may"
    MUST_NOT = "must_not"
    SHOULD_NOT = "should_not"


@dataclass
class CommitmentPrimitive:
    """A deontic commitment — obligation, permission, or prohibition.

    FPF A.2.8: commitments are scoped, have validity windows,
    require evidence refs, and have adjudication hooks.
    Separate from admissibility gates (those are structural,
    commitments are deontic).
    """
    commitment_id: str
    label: str
    modality: DeonticModality
    context_id: str
    subject: str = ""
    scope: str = ""
    validity_window: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    adjudication_hook: str | None = None

    @property
    def is_binding(self) -> bool:
        return self.modality in (DeonticModality.MUST, DeonticModality.MUST_NOT)


# ---------------------------------------------------------------------------
# A.21 — GateProfilization: OperationalGate
# ---------------------------------------------------------------------------

class GateDecision(Enum):
    """Gate outcome lattice — FPF A.21: abstain ≤ pass ≤ degrade ≤ block.

    ABSTAIN = insufficient evidence to evaluate (resolvable by collecting evidence)
    PASS    = all checks satisfied
    DEGRADE = partial checks satisfied (proceed with caution)
    BLOCK   = hard denial (cannot proceed regardless of evidence)
    """
    ABSTAIN = "abstain"
    PASS = "pass"
    DEGRADE = "degrade"
    BLOCK = "block"


@dataclass
class GateCheck:
    """A single check within a gate profile."""
    check_id: str
    description: str
    required_evidence: list[str] = field(default_factory=list)

    def evaluate(self, available_evidence: set[str]) -> GateDecision:
        missing = set(self.required_evidence) - available_evidence
        if not missing:
            return GateDecision.PASS
        if len(missing) < len(self.required_evidence):
            return GateDecision.DEGRADE
        return GateDecision.ABSTAIN


@dataclass
class GatePrimitive:
    """An operational gate that aggregates checks into a decision.

    FPF A.21: gates aggregate GateChecks via join-semilattice.
    Gate ≠ commitment (structural vs deontic).
    Gates are the deterministic validation layer before action.
    """
    gate_id: str
    label: str
    context_id: str
    checks: list[GateCheck] = field(default_factory=list)
    fail_closed: bool = True

    def evaluate(self, available_evidence: set[str]) -> GateDecision:
        if not self.checks:
            return GateDecision.ABSTAIN if self.fail_closed else GateDecision.PASS

        decisions = [c.evaluate(available_evidence) for c in self.checks]

        if GateDecision.ABSTAIN in decisions:
            return GateDecision.ABSTAIN
        if GateDecision.DEGRADE in decisions:
            return GateDecision.DEGRADE
        return GateDecision.PASS

    def missing_evidence(self, available_evidence: set[str]) -> list[str]:
        """Return only the evidence this gate is missing."""
        missing: set[str] = set()
        for c in self.checks:
            missing.update(set(c.required_evidence) - available_evidence)
        return sorted(missing)


# ---------------------------------------------------------------------------
# A.10 — Evidence Graph + A.2.4 EvidenceRole + B.3 F-G-R
# ---------------------------------------------------------------------------

class Freshness(Enum):
    """Evidence freshness — normalized from free text. #20."""
    CURRENT = "current"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass
class FGR:
    """Trust tuple — FPF B.3 Trust & Assurance Calculus.

    F = formality level (how rigorous the evidence)
    G = claim scope (how broad the claim)
    R = reliability (how dependable the evidence source)
    """
    formality: float = 0.0
    scope: float = 0.0
    reliability: float = 0.0

    def sufficient(self, min_f: float = 0.0, min_r: float = 0.0) -> bool:
        return self.formality >= min_f and self.reliability >= min_r


@dataclass
class EvidencePrimitive:
    """An evidence record with provenance and trust assessment.

    FPF A.10: claims must be supported by evidence with traceability.
    FPF B.3: trust is computed as F-G-R tuple, not a feeling.
    FPF B.3.4: evidence decays — freshness matters.
    """
    evidence_id: str
    label: str
    context_id: str
    claim: str = ""
    source: str = ""
    fgr: FGR = field(default_factory=FGR)
    freshness: Freshness = Freshness.UNKNOWN
    ttl_steps: int | None = None
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# A.3.3 U.Dynamics + B.4 Canonical Evolution Loop
# ---------------------------------------------------------------------------

@dataclass
class TransitionPrimitive:
    """A state transition in the semantic map.

    FPF A.3.3 (U.Dynamics): state evolution as law of change.
    FPF B.4: canonical evolution loop (Run-Observe-Refine-Deploy).
    FPF A.2.5 (U.RoleStateGraph): roles have state machines.

    Transitions connect states. Guards on transitions are evaluated
    before the transition fires.
    """
    transition_id: str
    label: str
    context_id: str
    from_state: str
    to_state: str
    required_gate_id: str | None = None
    required_evidence: list[str] = field(default_factory=list)
    readiness_refs: list[str] = field(default_factory=list)
    guard_expression: str = ""


# ---------------------------------------------------------------------------
# E.17 MVPK — Multi-View Publication
# ---------------------------------------------------------------------------

class PublicationFace(Enum):
    """MVPK faces — same content, different audiences."""
    PLAIN = "plain"
    TECHNICAL = "technical"
    INTEROP = "interop"
    ASSURANCE = "assurance"


@dataclass
class PublicationPrimitive:
    """A publication surface for making results visible.

    FPF E.17 (MVPK): consistent views from the same underlying model.
    Publication faces do not add new semantics — they are views.
    Out of the default step path — only consulted for publish moves.
    """
    publication_id: str
    label: str
    context_id: str
    face: PublicationFace = PublicationFace.TECHNICAL
    audience: str = ""
    source_work_ids: list[str] = field(default_factory=list)
    required_gate_id: str | None = None
