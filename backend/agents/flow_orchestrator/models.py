"""
Flow Orchestrator Agent - Data Models

Models for patient placement decisions and flow optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.reasoning.mcda import MCDAScores
from backend.reasoning.decision_engine import ActionType


class PlacementStatus(str, Enum):
    """Status of a placement option."""
    AVAILABLE = "available"
    CONSTRAINED = "constrained"  
    UNAVAILABLE = "unavailable"
    PENDING = "pending"


@dataclass
class PlacementOption:
    """
    A possible patient placement option with associated scores.
    
    Represents one potential destination for a patient with
    MCDA-based scoring and availability information.
    """
    option_id: str
    unit: str  # ICU, Ward, ED, etc.
    bed_id: Optional[str] = None
    status: PlacementStatus = PlacementStatus.AVAILABLE
    mcda_scores: Optional[MCDAScores] = None
    capacity_score: float = 0.0
    staff_ratio: float = 0.0
    estimated_wait_minutes: int = 0
    constraints: List[str] = field(default_factory=list)
    notes: str = ""
    
    @property
    def is_viable(self) -> bool:
        """Check if this option is currently viable."""
        return self.status in [PlacementStatus.AVAILABLE, PlacementStatus.PENDING]
    
    @property
    def composite_viability_score(self) -> float:
        """Calculate overall viability score."""
        if not self.is_viable:
            return 0.0
        
        base = self.mcda_scores.composite_score if self.mcda_scores else 50.0
        
        # Penalize long waits
        if self.estimated_wait_minutes > 60:
            base *= 0.7
        elif self.estimated_wait_minutes > 30:
            base *= 0.85
        
        # Penalize constraints
        base *= max(0.5, 1 - len(self.constraints) * 0.1)
        
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "unit": self.unit,
            "bed_id": self.bed_id,
            "status": self.status.value,
            "mcda_scores": self.mcda_scores.to_dict() if self.mcda_scores else None,
            "capacity_score": round(self.capacity_score, 2),
            "staff_ratio": round(self.staff_ratio, 3),
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "constraints": self.constraints,
            "notes": self.notes,
            "is_viable": self.is_viable,
            "composite_viability_score": round(self.composite_viability_score, 2)
        }


@dataclass
class ScenarioOutcome:
    """
    Result of a what-if scenario simulation.
    
    Used to compare outcomes of different timing decisions,
    e.g., "what happens if we wait 15 minutes?"
    """
    scenario_id: str
    description: str
    wait_time_minutes: int
    predicted_capacity_score: float
    predicted_wait_for_bed: int  # Additional minutes to wait for bed
    risk_level: str  # LOW, MEDIUM, HIGH
    expected_benefits: List[str] = field(default_factory=list)
    expected_risks: List[str] = field(default_factory=list)
    probability_of_better_outcome: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "wait_time_minutes": self.wait_time_minutes,
            "predicted_capacity_score": round(self.predicted_capacity_score, 2),
            "predicted_wait_for_bed": self.predicted_wait_for_bed,
            "risk_level": self.risk_level,
            "expected_benefits": self.expected_benefits,
            "expected_risks": self.expected_risks,
            "probability_of_better_outcome": round(self.probability_of_better_outcome, 3)
        }
    
    @property
    def is_favorable(self) -> bool:
        """Check if this scenario is worth pursuing."""
        return (
            self.probability_of_better_outcome > 0.6 and
            self.risk_level != "HIGH"
        )


@dataclass
class FlowRecommendation:
    """
    Output from the Flow Orchestrator Agent.
    
    This is the primary data contract for flow decisions,
    consumed by the Escalation agent for final decision making.
    
    As specified in WORK_ALLOCATION.md:
    - patient_id: str
    - recommended_action: ActionType
    - alternative_options: List[PlacementOption]
    - confidence: float
    - mcda_scores: MCDAScores
    """
    patient_id: str
    recommended_action: ActionType
    recommended_unit: Optional[str] = None
    alternative_options: List[PlacementOption] = field(default_factory=list)
    confidence: float = 0.8
    mcda_scores: Optional[MCDAScores] = None
    reasoning: str = ""
    scenarios_analyzed: List[ScenarioOutcome] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Additional context
    wait_recommendation: Optional[int] = None  # Minutes to wait, if applicable
    urgent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "recommended_action": self.recommended_action.value,
            "recommended_unit": self.recommended_unit,
            "alternative_options": [opt.to_dict() for opt in self.alternative_options],
            "confidence": round(self.confidence, 3),
            "mcda_scores": self.mcda_scores.to_dict() if self.mcda_scores else None,
            "reasoning": self.reasoning,
            "scenarios_analyzed": [s.to_dict() for s in self.scenarios_analyzed],
            "timestamp": self.timestamp.isoformat(),
            "wait_recommendation": self.wait_recommendation,
            "urgent": self.urgent
        }
    
    @property
    def priority_level(self) -> str:
        """Get priority level from MCDA scores."""
        if self.mcda_scores:
            return self.mcda_scores.priority_level
        return "MEDIUM"
    
    @property
    def best_alternative(self) -> Optional[PlacementOption]:
        """Get the best alternative if primary recommendation fails."""
        viable = [opt for opt in self.alternative_options if opt.is_viable]
        if not viable:
            return None
        return max(viable, key=lambda x: x.composite_viability_score)
