"""
Multi-Criteria Decision Analysis (MCDA) Framework

Implements weighted decision analysis for patient flow optimization.

Criteria:
- Safety: Patient safety risk (higher = more urgent to act)
- Urgency: Time-sensitivity of the decision
- Capacity: Available resources (beds, staff)
- Impact: Downstream effects of the decision

The MCDA framework produces weighted scores that inform the
Flow Orchestrator's placement recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class CriterionType(str, Enum):
    """The four main decision criteria."""
    SAFETY = "safety"
    URGENCY = "urgency"
    CAPACITY = "capacity"
    IMPACT = "impact"


@dataclass
class MCDAWeights:
    """
    Configurable weights for each decision criterion.
    
    Weights should sum to 1.0 for normalized scoring.
    Default weights prioritize safety and urgency.
    """
    safety: float = 0.35
    urgency: float = 0.30
    capacity: float = 0.20
    impact: float = 0.15
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        total = self.safety + self.urgency + self.capacity + self.impact
        if abs(total - 1.0) > 0.01:
            # Auto-normalize if weights don't sum to 1
            self.safety /= total
            self.urgency /= total
            self.capacity /= total
            self.impact /= total
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "safety": self.safety,
            "urgency": self.urgency,
            "capacity": self.capacity,
            "impact": self.impact
        }
    
    @classmethod
    def for_emergency(cls) -> "MCDAWeights":
        """Weights optimized for emergency situations."""
        return cls(safety=0.45, urgency=0.35, capacity=0.12, impact=0.08)
    
    @classmethod
    def for_routine(cls) -> "MCDAWeights":
        """Weights optimized for routine decisions."""
        return cls(safety=0.25, urgency=0.20, capacity=0.30, impact=0.25)
    
    @classmethod
    def for_overcrowding(cls) -> "MCDAWeights":
        """Weights optimized when capacity is constrained."""
        return cls(safety=0.30, urgency=0.25, capacity=0.30, impact=0.15)


@dataclass
class MCDAScores:
    """
    Container for MCDA scores - the primary output of the MCDA analysis.
    
    Each score is 0-100 where higher means:
    - Safety: Higher patient safety concern (needs action)
    - Urgency: More time-sensitive
    - Capacity: Better capacity availability
    - Impact: Higher downstream impact
    
    The composite_score is weighted average of all criteria.
    """
    safety: float
    urgency: float
    capacity: float
    impact: float
    composite_score: float
    weights_used: MCDAWeights = field(default_factory=MCDAWeights)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "safety": round(self.safety, 2),
            "urgency": round(self.urgency, 2),
            "capacity": round(self.capacity, 2),
            "impact": round(self.impact, 2),
            "composite_score": round(self.composite_score, 2),
            "weights_used": self.weights_used.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }
    
    @property
    def priority_level(self) -> str:
        """Categorize the priority based on composite score."""
        if self.composite_score >= 80:
            return "CRITICAL"
        elif self.composite_score >= 60:
            return "HIGH"
        elif self.composite_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    @property
    def dominant_factor(self) -> str:
        """Identify which criterion contributes most to the score."""
        weighted = {
            "safety": self.safety * self.weights_used.safety,
            "urgency": self.urgency * self.weights_used.urgency,
            "capacity": self.capacity * self.weights_used.capacity,
            "impact": self.impact * self.weights_used.impact
        }
        return max(weighted, key=weighted.get)


@dataclass
class TradeOffAnalysis:
    """Analysis of trade-offs between different options."""
    option_id: str
    scores: MCDAScores
    trade_offs: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "scores": self.scores.to_dict(),
            "trade_offs": self.trade_offs,
            "risks": self.risks,
            "benefits": self.benefits
        }


class MCDAAnalyzer:
    """
    Core MCDA analysis engine.
    
    Calculates weighted scores for patient placement decisions
    and performs trade-off analysis between options.
    """
    
    def __init__(self, weights: Optional[MCDAWeights] = None):
        self.weights = weights or MCDAWeights()
    
    def set_weights(self, weights: MCDAWeights) -> None:
        """Update the weighting configuration."""
        self.weights = weights
    
    def calculate_scores(
        self,
        safety_score: float,
        urgency_score: float,
        capacity_score: float,
        impact_score: float
    ) -> MCDAScores:
        """
        Calculate MCDA scores from raw criterion scores.
        """
        # Normalize inputs to 0-100 range
        safety = max(0, min(100, safety_score))
        urgency = max(0, min(100, urgency_score))
        capacity = max(0, min(100, capacity_score))
        impact = max(0, min(100, impact_score))
        
        # Calculate weighted composite score
        composite = (
            safety * self.weights.safety +
            urgency * self.weights.urgency +
            capacity * self.weights.capacity +
            impact * self.weights.impact
        )
        
        return MCDAScores(
            safety=safety,
            urgency=urgency,
            capacity=capacity,
            impact=impact,
            composite_score=composite,
            weights_used=self.weights
        )
    
    def calculate_from_context(
        self,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any],
        risk_context: Optional[Dict[str, Any]] = None
    ) -> MCDAScores:
        """
        Calculate MCDA scores from patient and capacity context.
        """
        safety_score = self._calculate_safety_score(patient_context, risk_context)
        urgency_score = self._calculate_urgency_score(patient_context)
        capacity_score = capacity_context.get("capacity_score", 50)
        impact_score = self._calculate_impact_score(patient_context, capacity_context)
        
        return self.calculate_scores(
            safety_score=safety_score,
            urgency_score=urgency_score,
            capacity_score=capacity_score,
            impact_score=impact_score
        )
    
    def _calculate_safety_score(
        self,
        patient_context: Dict[str, Any],
        risk_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate safety score from patient risk factors."""
        base_score = 50.0
        
        if risk_context:
            risk_score = risk_context.get("risk_score", 50)
            trajectory = risk_context.get("trajectory", "stable")
            base_score = risk_score
            if trajectory == "deteriorating":
                base_score = min(100, base_score * 1.3)
            elif trajectory == "improving":
                base_score = max(0, base_score * 0.8)
        else:
            acuity = patient_context.get("acuity_level", 3)
            base_score = acuity * 20
        
        if patient_context.get("requires_monitoring", False):
            base_score = min(100, base_score + 15)
        if patient_context.get("isolation_required", False):
            base_score = min(100, base_score + 10)
        
        return base_score
    
    def _calculate_urgency_score(self, patient_context: Dict[str, Any]) -> float:
        """Calculate urgency based on time factors."""
        base_score = 50.0
        wait_minutes = patient_context.get("wait_time_minutes", 0)
        
        if wait_minutes > 240:
            base_score = 90
        elif wait_minutes > 120:
            base_score = 70
        elif wait_minutes > 60:
            base_score = 55
        else:
            base_score = 30
        
        if patient_context.get("is_emergency", False):
            base_score = min(100, base_score + 30)
        if patient_context.get("needs_surgery", False):
            base_score = min(100, base_score + 20)
        if patient_context.get("time_critical_condition", False):
            base_score = 95
        
        return base_score
    
    def _calculate_impact_score(
        self,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any]
    ) -> float:
        """Calculate downstream impact of the decision."""
        base_score = 50.0
        
        if patient_context.get("boarding_in_ed", False):
            base_score = min(100, base_score + 25)
        if patient_context.get("pending_procedures", []):
            base_score = min(100, base_score + 15)
        
        occupancy = capacity_context.get("current_occupancy", 0.7)
        if occupancy > 0.9:
            base_score = min(100, base_score * 1.3)
        elif occupancy > 0.8:
            base_score = min(100, base_score * 1.15)
        
        return base_score
    
    def compare_options(
        self,
        options: List[Tuple[str, MCDAScores]]
    ) -> List[TradeOffAnalysis]:
        """Compare multiple placement options and analyze trade-offs."""
        if not options:
            return []
        
        analyses = []
        best = {
            "safety": max(opt[1].safety for opt in options),
            "urgency": max(opt[1].urgency for opt in options),
            "capacity": max(opt[1].capacity for opt in options),
            "impact": max(opt[1].impact for opt in options)
        }
        
        for option_id, scores in options:
            trade_offs = []
            risks = []
            benefits = []
            
            if scores.safety >= best["safety"] * 0.9:
                benefits.append("High safety consideration")
            elif scores.safety < best["safety"] * 0.7:
                risks.append("Lower safety priority than alternatives")
            
            if scores.urgency >= best["urgency"] * 0.9:
                benefits.append("Addresses urgency effectively")
            elif scores.urgency < best["urgency"] * 0.7:
                trade_offs.append("May delay urgent needs")
            
            if scores.capacity >= best["capacity"] * 0.9:
                benefits.append("Good resource availability")
            elif scores.capacity < best["capacity"] * 0.7:
                trade_offs.append("Capacity constraints may limit placement")
            
            if scores.impact >= best["impact"] * 0.9:
                benefits.append("Positive downstream impact")
            elif scores.impact < best["impact"] * 0.7:
                trade_offs.append("Limited flow improvement")
            
            analyses.append(TradeOffAnalysis(
                option_id=option_id,
                scores=scores,
                trade_offs=trade_offs,
                risks=risks,
                benefits=benefits
            ))
        
        analyses.sort(key=lambda a: a.scores.composite_score, reverse=True)
        return analyses
    
    def get_recommendation(
        self,
        options: List[Tuple[str, MCDAScores]]
    ) -> Tuple[str, MCDAScores, str]:
        """Get the recommended option with explanation."""
        if not options:
            return ("none", MCDAScores(0, 0, 0, 0, 0), "No options available")
        
        analyses = self.compare_options(options)
        best = analyses[0]
        
        explanation = f"Recommended '{best.option_id}' with score {best.scores.composite_score:.1f} "
        explanation += f"(Priority: {best.scores.priority_level}). "
        explanation += f"Dominant factor: {best.scores.dominant_factor}. "
        
        if best.benefits:
            explanation += f"Benefits: {', '.join(best.benefits)}."
        
        return (best.option_id, best.scores, explanation)


# Alias for compatibility
MCDACalculator = MCDAAnalyzer
