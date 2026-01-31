"""
Reasoning Module

Multi-Criteria Decision Analysis (MCDA) and Decision Engine
for the AdaptiveCare patient flow system.

Exports:
- MCDAAnalyzer/MCDACalculator: Core MCDA scoring engine
- MCDAScores, MCDAWeights: Data models
- DecisionEngine: Synthesizes decisions with uncertainty
- ActionType: Action type enumeration
- LLMReasoning: LLM-based explanation generation
"""

from .mcda import (
    MCDAAnalyzer,
    MCDACalculator,
    MCDAScores,
    MCDAWeights,
    TradeOffAnalysis,
    CriterionType,
)

from .decision_engine import (
    DecisionEngine,
    DecisionOutput,
    ActionType,
    ConfidenceLevel,
    UncertaintyMetrics,
    WaitProbability,
    UncertaintyQuantifier,
    WaitProbabilityCalculator,
    create_decision_engine,
)

try:
    from .llm_reasoning import LLMReasoning
except ImportError:
    LLMReasoning = None  # Optional - requires additional dependencies

__all__ = [
    # MCDA
    "MCDAAnalyzer",
    "MCDACalculator",
    "MCDAScores",
    "MCDAWeights",
    "TradeOffAnalysis",
    "CriterionType",
    # Decision Engine
    "DecisionEngine",
    "DecisionOutput",
    "ActionType",
    "ConfidenceLevel",
    "UncertaintyMetrics",
    "WaitProbability",
    "UncertaintyQuantifier",
    "WaitProbabilityCalculator",
    "create_decision_engine",
    # LLM
    "LLMReasoning",
]
