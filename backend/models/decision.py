from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid


class ActionType(str, Enum):
    ESCALATE = "escalate"
    OBSERVE = "observe"
    DELAY = "delay"
    REPRIORITIZE = "reprioritize"
    TRANSFER = "transfer"
    DISCHARGE = "discharge"


class RiskTrajectory(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    CRITICAL = "critical"


class MCDAScores(BaseModel):
    safety_score: float = Field(..., ge=0, le=100)
    urgency_score: float = Field(..., ge=0, le=100)
    capacity_score: float = Field(..., ge=0, le=100)
    impact_score: float = Field(..., ge=0, le=100)
    weighted_total: float = Field(..., ge=0, le=100)


class Decision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    agent_name: str
    action: ActionType
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskAssessment(BaseModel):
    patient_id: str
    risk_score: float = Field(..., ge=0, le=100)
    trajectory: RiskTrajectory
    confidence: float = Field(..., ge=0, le=1)
    contributing_factors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CapacityAssessment(BaseModel):
    unit: str
    current_occupancy: float = Field(..., ge=0, le=1)
    staff_ratio: float
    available_beds: int
    capacity_score: float = Field(..., ge=0, le=100)
    predicted_availability: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PlacementOption(BaseModel):
    destination: str
    bed_id: Optional[str] = None
    estimated_wait_minutes: int = 0
    confidence: float = Field(..., ge=0, le=1)
    mcda_scores: Optional[MCDAScores] = None


class FlowRecommendation(BaseModel):
    patient_id: str
    recommended_destination: str
    recommended_action: ActionType
    alternative_options: List[PlacementOption] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    mcda_scores: MCDAScores
    scenario_analysis: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EscalationDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    action: ActionType
    destination: Optional[str] = None
    reasoning: str
    mcda_breakdown: MCDAScores
    confidence: float = Field(..., ge=0, le=1)
    alternatives_considered: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
