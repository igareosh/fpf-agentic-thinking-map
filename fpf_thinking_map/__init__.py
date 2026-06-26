"""FPF Thinking Map — compiled semantic substrate for agentic traversal.

FPF (First Principles Framework) semi-encoded into a thinking map where:
- FPF supplies the semantic field (primitives)
- inputs fill variables (binding)
- the LLM traverses the map (traversal)
- deterministic guards + propositional logic constrain invalid moves
- outcomes are decided by the agent inside that bounded semantic structure
"""

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
    SemanticFloor,
    FLOOR_BASE_TTL,
    EvidencePrimitive,
    FGR,
    Freshness,
    TransitionPrimitive,
    PublicationPrimitive,
    PublicationFace,
)
from fpf_thinking_map.state import (
    RuntimeBinding,
    SemanticMap,
    ActiveState,
    MoveTrace,
)
from fpf_thinking_map.guards import (
    GuardEngine,
    GuardVerdict,
    GuardScope,
    Guard,
    GuardResult,
)
from fpf_thinking_map.logic import (
    LogicLayer,
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
    DecisionRule,
)
from fpf_thinking_map.traversal import ThinkingMapTraversal, Outcome, OutcomeKind
