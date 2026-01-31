"""
Flow Orchestrator Agent

Recommends optimal patient placement using MCDA analysis and
what-if scenario simulation.

Exports:
- FlowOrchestratorAgent: Main agent class
- FlowRecommendation: Output data model
- PlacementOption, ScenarioOutcome: Supporting models
- create_flow_orchestrator: Helper for testing
"""

from .models import (
    FlowRecommendation,
    PlacementOption,
    PlacementStatus,
    ScenarioOutcome,
)

from .scenarios import (
    ScenarioSimulator,
    ScenarioComparator,
)

from .agent import (
    FlowOrchestratorAgent,
    create_flow_orchestrator,
)

__all__ = [
    # Agent
    "FlowOrchestratorAgent",
    "create_flow_orchestrator",
    # Models
    "FlowRecommendation",
    "PlacementOption",
    "PlacementStatus",
    "ScenarioOutcome",
    # Scenarios
    "ScenarioSimulator",
    "ScenarioComparator",
]
