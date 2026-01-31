"""
Flow Orchestrator Agent

Recommends optimal patient placement using MCDA analysis and
what-if scenario simulation.

This agent:
1. Reads RiskAssessment and CapacityAssessment from other agents
2. Uses MCDA to score placement options
3. Runs what-if scenarios ("what if we wait 15 min?")
4. Produces FlowRecommendation with alternatives
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .models import (
    FlowRecommendation, 
    PlacementOption, 
    ScenarioOutcome,
    PlacementStatus
)
from .scenarios import ScenarioSimulator, ScenarioComparator
from backend.reasoning.mcda import MCDAScores, MCDAAnalyzer, MCDAWeights
from backend.reasoning.decision_engine import ActionType, DecisionEngine


# ============================================================================
# Minimal BaseAgent stub (will be replaced when Ashu's base_agent.py is ready)
# ============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    NOTE: This is a temporary stub. The real implementation will be in
    backend/agents/base_agent.py once the core infrastructure is ready.
    """
    
    def __init__(self, event_bus=None, state_manager=None):
        self.event_bus = event_bus
        self.state = state_manager
    
    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant data from current hospital state."""
        pass
    
    @abstractmethod
    async def decide(self, observations: Dict[str, Any]) -> Any:
        """Make a decision based on observations."""
        pass
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the observe-decide cycle."""
        observations = await self.observe(context)
        decision = await self.decide(observations)
        
        if self.event_bus:
            await self.event_bus.publish(
                f"{self.__class__.__name__}.decision", 
                decision
            )
        
        return decision


# ============================================================================
# Flow Orchestrator Agent
# ============================================================================

class FlowOrchestratorAgent(BaseAgent):
    """
    Flow Orchestrator Agent - recommends optimal patient placement.
    
    Responsibilities:
    - Evaluate placement options using MCDA
    - Run what-if scenarios for timing decisions
    - Produce FlowRecommendation with alternatives
    - Consider both immediate and delayed placement
    
    Usage:
        agent = FlowOrchestratorAgent()
        
        # With full context
        recommendation = agent.get_recommendation(
            patient_id="P001",
            patient_context={"acuity_level": 3, "wait_time_minutes": 45},
            capacity_assessments={"ICU": icuAssessment, "Ward": wardAssessment},
            risk_assessment={"risk_score": 65, "trajectory": "stable"}
        )
        
        # Simplified
        recommendation = agent.get_recommendation(patient_id="P001")
    """
    
    def __init__(self, event_bus=None, state_manager=None, weights: Optional[MCDAWeights] = None):
        super().__init__(event_bus, state_manager)
        self.mcda_analyzer = MCDAAnalyzer(weights)
        self.decision_engine = DecisionEngine(weights)
        self.scenario_simulator = ScenarioSimulator(self.mcda_analyzer)
        self.scenario_comparator = ScenarioComparator()
        
        # Will hold capacity assessments from Capacity Intelligence Agent
        self._capacity_cache: Dict[str, Any] = {}
        self._risk_cache: Dict[str, Any] = {}
    
    def set_capacity_assessments(self, assessments: Dict[str, Any]) -> None:
        """Update cached capacity assessments from Capacity Intelligence Agent."""
        self._capacity_cache = assessments
    
    def set_risk_assessment(self, patient_id: str, risk: Dict[str, Any]) -> None:
        """Update cached risk assessment from Risk Monitor Agent."""
        self._risk_cache[patient_id] = risk
    
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather data for flow decision.
        
        Reads from:
        - Capacity Intelligence Agent (capacity assessments)
        - Risk Monitor Agent (patient risk assessments)
        - State Manager (if available)
        
        Args:
            context: Must contain patient_id, may contain other data
        
        Returns:
            Observations dict with patient, capacity, and risk data
        """
        patient_id = context.get("patient_id")
        
        observations = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get patient context from request or state
        patient_context = context.get("patient_context", {})
        if not patient_context and self.state:
            # Try to get from state manager
            patient_data = await self.state.get(f"patient:{patient_id}")
            if patient_data:
                patient_context = patient_data
        
        observations["patient"] = patient_context or self._get_demo_patient_context()
        
        # Get capacity assessments
        capacity = context.get("capacity_assessments")
        if not capacity:
            capacity = self._capacity_cache or self._get_demo_capacity()
        
        observations["capacity"] = capacity
        
        # Get risk assessment
        risk = context.get("risk_assessment")
        if not risk and patient_id:
            risk = self._risk_cache.get(patient_id)
        
        observations["risk"] = risk or {"risk_score": 50, "trajectory": "stable"}
        
        # Get available units
        available_units = []
        for unit_name, cap_data in capacity.items():
            if isinstance(cap_data, dict):
                score = cap_data.get("capacity_score", 50)
            else:
                score = getattr(cap_data, "capacity_score", 50)
            
            if score > 20:  # Has some capacity
                available_units.append(unit_name)
        
        observations["available_units"] = available_units
        
        return observations
    
    async def decide(self, observations: Dict[str, Any]) -> FlowRecommendation:
        """
        Make flow/placement recommendation based on observations.
        
        Uses MCDA to score options and scenarios to evaluate timing.
        
        Returns:
            FlowRecommendation with action, alternatives, and MCDA scores
        """
        patient_id = observations.get("patient_id", "unknown")
        patient_context = observations.get("patient", {})
        capacity_data = observations.get("capacity", {})
        risk_data = observations.get("risk", {})
        available_units = observations.get("available_units", [])
        
        # Step 1: Prepare unit data for scenario simulation
        unit_data_list = []
        for unit_name, cap_data in capacity_data.items():
            if isinstance(cap_data, dict):
                unit_data_list.append({
                    "unit": unit_name,
                    "capacity_score": cap_data.get("capacity_score", 50),
                    "current_occupancy": cap_data.get("current_occupancy", 0.7),
                    "staff_ratio": cap_data.get("staff_ratio", 1.0),
                    "predicted_availability": cap_data.get("predicted_availability")
                })
            else:
                unit_data_list.append({
                    "unit": unit_name,
                    "capacity_score": getattr(cap_data, "capacity_score", 50),
                    "current_occupancy": getattr(cap_data, "current_occupancy", 0.7),
                    "staff_ratio": getattr(cap_data, "staff_ratio", 1.0),
                    "predicted_availability": getattr(cap_data, "predicted_availability", None)
                })
        
        # Step 2: Simulate placement options
        placement_options = self.scenario_simulator.simulate_placement_scenarios(
            patient_context=patient_context,
            available_units=unit_data_list,
            risk_context=risk_data
        )
        
        # Step 3: Run timing analysis (what-if scenarios)
        best_capacity = max((u.get("capacity_score", 0) for u in unit_data_list), default=50)
        capacity_context = {
            "capacity_score": best_capacity,
            "predicted_availability": any(u.get("predicted_availability") for u in unit_data_list)
        }
        
        timing_scenarios = self.scenario_simulator.run_timing_analysis(
            patient_context=patient_context,
            capacity_context=capacity_context
        )
        
        # Step 4: Determine best option
        best_placement, alternatives, placement_reasoning = \
            self.scenario_comparator.compare_placement_options(placement_options)
        
        best_timing, timing_reasoning = \
            self.scenario_comparator.compare_wait_scenarios(timing_scenarios)
        
        # Step 5: Calculate final MCDA scores
        if best_placement and best_placement.mcda_scores:
            mcda_scores = best_placement.mcda_scores
        else:
            mcda_scores = self.mcda_analyzer.calculate_from_context(
                patient_context=patient_context,
                capacity_context=capacity_context,
                risk_context=risk_data
            )
        
        # Step 6: Determine action and confidence
        action, recommended_unit, confidence = self._determine_action(
            best_placement=best_placement,
            best_timing=best_timing,
            mcda_scores=mcda_scores,
            patient_context=patient_context
        )
        
        # Step 7: Build reasoning
        reasoning = f"{placement_reasoning} {timing_reasoning}"
        
        return FlowRecommendation(
            patient_id=patient_id,
            recommended_action=action,
            recommended_unit=recommended_unit,
            alternative_options=alternatives,
            confidence=confidence,
            mcda_scores=mcda_scores,
            reasoning=reasoning.strip(),
            scenarios_analyzed=timing_scenarios,
            wait_recommendation=best_timing.wait_time_minutes if best_timing and best_timing.wait_time_minutes > 0 else None,
            urgent=mcda_scores.priority_level in ["CRITICAL", "HIGH"]
        )
    
    def _determine_action(
        self,
        best_placement: Optional[PlacementOption],
        best_timing: Optional[ScenarioOutcome],
        mcda_scores: MCDAScores,
        patient_context: Dict[str, Any]
    ) -> tuple:
        """Determine recommended action, unit, and confidence."""
        
        # Critical priority always escalates
        if mcda_scores.priority_level == "CRITICAL":
            return (ActionType.ESCALATE, None, 0.9)
        
        # Check if waiting is recommended
        if best_timing and best_timing.is_favorable and best_timing.wait_time_minutes > 0:
            return (ActionType.DELAY, None, best_timing.probability_of_better_outcome)
        
        # Check placement viability
        if best_placement and best_placement.is_viable:
            unit = best_placement.unit
            confidence = min(0.95, best_placement.composite_viability_score / 100)
            
            current_location = patient_context.get("current_location", "ED")
            if current_location == "ED":
                return (ActionType.ADMIT, unit, confidence)
            else:
                return (ActionType.TRANSFER, unit, confidence)
        
        # Default to observe if no good options
        return (ActionType.OBSERVE, None, 0.6)
    
    # ========================================================================
    # Synchronous convenience methods
    # ========================================================================
    
    def get_recommendation(
        self,
        patient_id: str,
        patient_context: Optional[Dict[str, Any]] = None,
        capacity_assessments: Optional[Dict[str, Any]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> FlowRecommendation:
        """
        Get flow recommendation (sync method).
        
        For testing and integration without async infrastructure.
        """
        import asyncio
        
        context = {
            "patient_id": patient_id,
            "patient_context": patient_context or self._get_demo_patient_context(),
            "capacity_assessments": capacity_assessments or self._get_demo_capacity(),
            "risk_assessment": risk_assessment
        }
        
        # Run async methods synchronously
        loop = asyncio.new_event_loop()
        try:
            observations = loop.run_until_complete(self.observe(context))
            recommendation = loop.run_until_complete(self.decide(observations))
            return recommendation
        finally:
            loop.close()
    
    def run_what_if(
        self,
        patient_id: str,
        wait_minutes: int,
        patient_context: Optional[Dict[str, Any]] = None,
        capacity_score: float = 50
    ) -> ScenarioOutcome:
        """
        Run a specific what-if scenario.
        
        Args:
            patient_id: Patient identifier
            wait_minutes: How long to wait
            patient_context: Patient data
            capacity_score: Current capacity score
        
        Returns:
            ScenarioOutcome with predictions
        """
        patient = patient_context or self._get_demo_patient_context()
        
        return self.scenario_simulator.simulate_wait_scenario(
            current_capacity_score=capacity_score,
            patient_context=patient,
            wait_minutes=wait_minutes,
            capacity_trend="stable"
        )
    
    def _get_demo_patient_context(self) -> Dict[str, Any]:
        """Get demo patient context for testing."""
        return {
            "patient_id": "P-DEMO-001",
            "acuity_level": 3,
            "wait_time_minutes": 45,
            "current_location": "ED",
            "trajectory": "stable",
            "preferred_unit": "Ward"
        }
    
    def _get_demo_capacity(self) -> Dict[str, Dict[str, Any]]:
        """Get demo capacity data for testing."""
        return {
            "ICU": {
                "capacity_score": 35,
                "current_occupancy": 0.85,
                "staff_ratio": 2.5,
                "predicted_availability": None
            },
            "Ward": {
                "capacity_score": 60,
                "current_occupancy": 0.70,
                "staff_ratio": 4.0,
                "predicted_availability": True
            },
            "ED": {
                "capacity_score": 25,
                "current_occupancy": 0.92,
                "staff_ratio": 3.0,
                "predicted_availability": None
            }
        }


# Convenience function for quick testing
def create_flow_orchestrator() -> FlowOrchestratorAgent:
    """Create a flow orchestrator agent for testing."""
    return FlowOrchestratorAgent()
