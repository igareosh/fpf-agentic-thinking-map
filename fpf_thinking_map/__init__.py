"""FPF Thinking Map — compiled semantic substrate for agentic traversal.

A structured board for LLM reasoning: the model navigates a pre-shaped
semantic field with deterministic guards and propositional logic constraints.
Evidence decays via TTL hop counter. The model reads small JSON slices and
picks moves — no re-reasoning about state the code already computed.

Modules:
  primitives  — 10 semantic objects + 5 semantic floors from FPF spec
  state       — runtime binding, active state, TTL tracking, per-move slices
  guards      — 9 deterministic guards (hard constraints, not LLM judgments)
  logic       — 6 propositional operators + freshness-aware decision rules
  traversal   — step engine with 10 lawful outcomes
  examples    — deploy decision scenarios demonstrating the full system
  verify      — 18-check self-verification harness
"""

# --- Primitives: the semantic field ---
from fpf_thinking_map.primitives import (
    ContextPrimitive,
    ContextBridge,
    RolePrimitive,
    AgencyLevel,
    RoleAssignment,
    WorkPrimitive,
    WorkPlanPrimitive,
    SpeechActPrimitive,
    SpeechActType,
    CommitmentPrimitive,
    DeonticModality,
    GatePrimitive,
    GateCheck,
    GateDecision,
    EvidencePrimitive,
    FGR,
    Freshness,
    SemanticFloor,
    FLOOR_BASE_TTL,
    TransitionPrimitive,
    PublicationPrimitive,
    PublicationFace,
)

# --- State: binding + active state + slicing ---
from fpf_thinking_map.state import (
    RuntimeBinding,
    SemanticMap,
    ActiveState,
    MoveTrace,
)

# --- Guards: deterministic hard constraints ---
from fpf_thinking_map.guards import (
    GuardEngine,
    GuardVerdict,
    GuardScope,
    Guard,
    GuardResult,
)

# --- Logic: propositional decision glue ---
from fpf_thinking_map.logic import (
    LogicLayer,
    DecisionRule,
    RuleKind,
    Prop,
    EvidencePresent,
    EvidenceFresh,
    GatePasses,
    GateBlocked,
    RoleActive,
    InState,
    CommitmentMet,
    HasMissingEvidence,
    RiskAbove,
    TransitionAvailable,
    CustomProp,
)

# --- Traversal: the step engine ---
from fpf_thinking_map.traversal import ThinkingMapTraversal, Outcome, OutcomeKind
