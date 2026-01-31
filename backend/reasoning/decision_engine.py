"""
Decision Engine

Core decision logic for the AdaptiveCare system.

Provides:
- Uncertainty quantification for decision confidence
- Safe-to-wait probability calculations
- Decision synthesis from multiple agent outputs
- Action recommendation with confidence levels
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import math

from .mcda import MCDAScores, MCDAWeights, MCDAAnalyzer


class ActionType(str, Enum):
    """Types of actions the system can recommend."""
    ESCALATE = "escalate"        # Immediate escalation required
    ADMIT = "admit"              # Admit to target unit
    TRANSFER = "transfer"        # Transfer between units
    OBSERVE = "observe"          # Continue observation
    DELAY = "delay"              # Safe to delay decision
    REPRIORITIZE = "reprioritize"  # Change priority


class ConfidenceLevel(str, Enum):
    """Confidence levels for decisions."""
    HIGH = "high"         # >0.8 confidence
    MEDIUM = "medium"     # 0.5-0.8 confidence
    LOW = "low"           # <0.5 confidence
    UNCERTAIN = "uncertain"  # Unable to determine


@dataclass
class UncertaintyMetrics:
    """Quantified uncertainty in the decision."""
    confidence: float  # 0-1
    confidence_level: ConfidenceLevel
    data_completeness: float  # 0-1, how complete the input data is
    model_uncertainty: float  # 0-1, inherent model uncertainty
    temporal_validity: float  # 0-1, how fresh the data is
    factors: List[str] = field(default_factory=list)  # Contributing uncertainty factors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 3),
            "confidence_level": self.confidence_level.value,
            "data_completeness": round(self.data_completeness, 3),
            "model_uncertainty": round(self.model_uncertainty, 3),
            "temporal_validity": round(self.temporal_validity, 3),
            "factors": self.factors
        }


@dataclass
class WaitProbability:
    """Safe-to-wait probability assessment."""
    safe_to_wait: bool
    probability: float  # 0-1
    recommended_wait_time: Optional[int] = None  # Minutes
    max_safe_wait: Optional[int] = None  # Minutes
    risk_if_waiting: str = ""
    benefit_if_waiting: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe_to_wait": self.safe_to_wait,
            "probability": round(self.probability, 3),
            "recommended_wait_time": self.recommended_wait_time,
            "max_safe_wait": self.max_safe_wait,
            "risk_if_waiting": self.risk_if_waiting,
            "benefit_if_waiting": self.benefit_if_waiting
        }


@dataclass
class DecisionOutput:
    """
    Complete decision output from the decision engine.
    
    This is consumed by the Escalation agent for final decision making.
    """
    patient_id: str
    recommended_action: ActionType
    target_unit: Optional[str] = None
    mcda_scores: Optional[MCDAScores] = None
    uncertainty: Optional[UncertaintyMetrics] = None
    wait_probability: Optional[WaitProbability] = None
    reasoning: str = ""
    alternatives: List[Tuple[ActionType, str]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "recommended_action": self.recommended_action.value,
            "target_unit": self.target_unit,
            "mcda_scores": self.mcda_scores.to_dict() if self.mcda_scores else None,
            "uncertainty": self.uncertainty.to_dict() if self.uncertainty else None,
            "wait_probability": self.wait_probability.to_dict() if self.wait_probability else None,
            "reasoning": self.reasoning,
            "alternatives": [(a.value, r) for a, r in self.alternatives],
            "timestamp": self.timestamp.isoformat()
        }


class UncertaintyQuantifier:
    """
    Quantifies uncertainty in decision inputs and outputs.
    
    Uses multiple signals to estimate decision confidence.
    """
    
    # Time thresholds for data freshness (in minutes)
    FRESH_THRESHOLD = 5
    STALE_THRESHOLD = 30
    EXPIRED_THRESHOLD = 60
    
    def quantify(
        self,
        mcda_scores: MCDAScores,
        data_timestamps: Optional[Dict[str, datetime]] = None,
        missing_fields: Optional[List[str]] = None
    ) -> UncertaintyMetrics:
        """
        Calculate uncertainty metrics for a decision.
        
        Args:
            mcda_scores: The MCDA scores being assessed
            data_timestamps: Timestamps of input data sources
            missing_fields: Any fields that are missing or estimated
        """
        factors = []
        
        # Data completeness
        missing = missing_fields or []
        if len(missing) == 0:
            data_completeness = 1.0
        else:
            # Penalize based on number and importance of missing fields
            penalty_per_field = 0.15
            data_completeness = max(0.3, 1.0 - len(missing) * penalty_per_field)
            factors.append(f"Missing data: {', '.join(missing)}")
        
        # Temporal validity
        temporal_validity = self._calculate_temporal_validity(data_timestamps)
        if temporal_validity < 0.7:
            factors.append("Some data sources are stale")
        
        # Model uncertainty based on score distribution
        model_uncertainty = self._calculate_model_uncertainty(mcda_scores)
        if model_uncertainty > 0.3:
            factors.append("High variance in MCDA criteria")
        
        # Calculate overall confidence
        confidence = (
            data_completeness * 0.4 +
            (1 - model_uncertainty) * 0.35 +
            temporal_validity * 0.25
        )
        
        # Determine confidence level
        if confidence >= 0.8:
            level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            level = ConfidenceLevel.MEDIUM
        elif confidence >= 0.2:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNCERTAIN
        
        return UncertaintyMetrics(
            confidence=confidence,
            confidence_level=level,
            data_completeness=data_completeness,
            model_uncertainty=model_uncertainty,
            temporal_validity=temporal_validity,
            factors=factors
        )
    
    def _calculate_temporal_validity(
        self, 
        timestamps: Optional[Dict[str, datetime]]
    ) -> float:
        """Calculate how fresh the data is."""
        if not timestamps:
            return 0.8  # Default assumption
        
        now = datetime.now()
        validities = []
        
        for source, ts in timestamps.items():
            age_minutes = (now - ts).total_seconds() / 60
            
            if age_minutes <= self.FRESH_THRESHOLD:
                validities.append(1.0)
            elif age_minutes <= self.STALE_THRESHOLD:
                # Linear decay
                validities.append(1.0 - (age_minutes - self.FRESH_THRESHOLD) / 
                                 (self.STALE_THRESHOLD - self.FRESH_THRESHOLD) * 0.3)
            elif age_minutes <= self.EXPIRED_THRESHOLD:
                # Faster decay
                validities.append(0.7 - (age_minutes - self.STALE_THRESHOLD) /
                                 (self.EXPIRED_THRESHOLD - self.STALE_THRESHOLD) * 0.4)
            else:
                validities.append(0.3)
        
        return sum(validities) / len(validities) if validities else 0.8
    
    def _calculate_model_uncertainty(self, scores: MCDAScores) -> float:
        """
        Estimate model uncertainty from score distribution.
        
        High variance between criteria suggests conflicting signals.
        """
        criteria = [scores.safety, scores.urgency, scores.capacity, scores.impact]
        mean = sum(criteria) / len(criteria)
        variance = sum((x - mean) ** 2 for x in criteria) / len(criteria)
        std_dev = math.sqrt(variance)
        
        # Normalize to 0-1 (std dev of 40 = high uncertainty)
        normalized = min(std_dev / 40, 1.0)
        
        return normalized


class WaitProbabilityCalculator:
    """
    Calculates safe-to-wait probabilities.
    
    Determines if it's safe to delay a placement decision and for how long.
    """
    
    def calculate(
        self,
        mcda_scores: MCDAScores,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any]
    ) -> WaitProbability:
        """
        Calculate whether it's safe to wait before acting.
        
        Args:
            mcda_scores: Current MCDA assessment
            patient_context: Patient information
            capacity_context: Current capacity state
        """
        # Base probability from MCDA scores
        # Higher urgency/safety = lower safe-to-wait probability
        urgency_factor = 1 - (mcda_scores.urgency / 100)
        safety_factor = 1 - (mcda_scores.safety / 100)
        
        base_probability = (urgency_factor * 0.5 + safety_factor * 0.5)
        
        # Adjust for capacity trends
        capacity_improving = capacity_context.get("predicted_availability") is not None
        if capacity_improving:
            base_probability = min(1.0, base_probability + 0.15)
        
        # Adjust for patient stability
        trajectory = patient_context.get("trajectory", "stable")
        if trajectory == "deteriorating":
            base_probability = max(0, base_probability - 0.3)
        elif trajectory == "improving":
            base_probability = min(1.0, base_probability + 0.1)
        
        # Calculate wait times
        recommended_wait = None
        max_safe_wait = None
        
        if base_probability >= 0.6:
            # Generally safe to wait
            recommended_wait = 15  # minutes
            max_safe_wait = 30
        elif base_probability >= 0.4:
            # Short wait possible
            recommended_wait = 5
            max_safe_wait = 15
        else:
            # Act now
            recommended_wait = 0
            max_safe_wait = 5
        
        # Generate explanations
        risk = self._explain_waiting_risk(mcda_scores, patient_context)
        benefit = self._explain_waiting_benefit(capacity_context)
        
        return WaitProbability(
            safe_to_wait=base_probability >= 0.5,
            probability=base_probability,
            recommended_wait_time=recommended_wait,
            max_safe_wait=max_safe_wait,
            risk_if_waiting=risk,
            benefit_if_waiting=benefit
        )
    
    def _explain_waiting_risk(
        self, 
        scores: MCDAScores, 
        patient_context: Dict[str, Any]
    ) -> str:
        """Generate explanation of waiting risks."""
        risks = []
        
        if scores.safety > 70:
            risks.append("patient safety concerns")
        if scores.urgency > 70:
            risks.append("time-sensitive condition")
        if patient_context.get("trajectory") == "deteriorating":
            risks.append("declining patient status")
        if patient_context.get("boarding_in_ed"):
            risks.append("ED boarding stress")
        
        if not risks:
            return "Low risk if waiting briefly"
        
        return f"Risks include: {', '.join(risks)}"
    
    def _explain_waiting_benefit(self, capacity_context: Dict[str, Any]) -> str:
        """Generate explanation of waiting benefits."""
        benefits = []
        
        predicted = capacity_context.get("predicted_availability")
        if predicted:
            benefits.append("bed expected to become available soon")
        
        if capacity_context.get("staff_ratio", 1) > 0.8:
            benefits.append("staffing levels may improve")
        
        if not benefits:
            return "Limited benefit to waiting"
        
        return f"Benefits: {', '.join(benefits)}"


class DecisionEngine:
    """
    Core decision engine that synthesizes all inputs into actionable decisions.
    
    Combines MCDA scores, uncertainty quantification, and wait probability
    to produce final decision recommendations.
    """
    
    def __init__(self, weights: Optional[MCDAWeights] = None):
        self.mcda_analyzer = MCDAAnalyzer(weights)
        self.uncertainty_quantifier = UncertaintyQuantifier()
        self.wait_calculator = WaitProbabilityCalculator()
    
    def make_decision(
        self,
        patient_id: str,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any],
        risk_context: Optional[Dict[str, Any]] = None,
        available_units: Optional[List[str]] = None
    ) -> DecisionOutput:
        """
        Make a placement/action decision for a patient.
        
        This is the main entry point for the decision engine.
        
        Args:
            patient_id: Patient identifier
            patient_context: Patient data (acuity, wait time, conditions)
            capacity_context: Capacity data from Capacity Intelligence
            risk_context: Risk data from Risk Monitor (optional)
            available_units: List of units with capacity (optional)
        
        Returns:
            DecisionOutput with recommendation and supporting analysis
        """
        # Step 1: Calculate MCDA scores
        mcda_scores = self.mcda_analyzer.calculate_from_context(
            patient_context=patient_context,
            capacity_context=capacity_context,
            risk_context=risk_context
        )
        
        # Step 2: Quantify uncertainty
        missing_fields = self._identify_missing_fields(patient_context, risk_context)
        uncertainty = self.uncertainty_quantifier.quantify(
            mcda_scores=mcda_scores,
            missing_fields=missing_fields
        )
        
        # Step 3: Calculate safe-to-wait probability
        wait_prob = self.wait_calculator.calculate(
            mcda_scores=mcda_scores,
            patient_context=patient_context,
            capacity_context=capacity_context
        )
        
        # Step 4: Determine recommended action
        action, target_unit, reasoning = self._determine_action(
            mcda_scores=mcda_scores,
            wait_prob=wait_prob,
            patient_context=patient_context,
            capacity_context=capacity_context,
            available_units=available_units
        )
        
        # Step 5: Generate alternatives
        alternatives = self._generate_alternatives(
            primary_action=action,
            mcda_scores=mcda_scores,
            wait_prob=wait_prob
        )
        
        return DecisionOutput(
            patient_id=patient_id,
            recommended_action=action,
            target_unit=target_unit,
            mcda_scores=mcda_scores,
            uncertainty=uncertainty,
            wait_probability=wait_prob,
            reasoning=reasoning,
            alternatives=alternatives
        )
    
    def _identify_missing_fields(
        self,
        patient_context: Dict[str, Any],
        risk_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify critical missing data fields."""
        missing = []
        
        if "acuity_level" not in patient_context:
            missing.append("acuity_level")
        if "wait_time_minutes" not in patient_context:
            missing.append("wait_time")
        if not risk_context:
            missing.append("risk_assessment")
        elif "risk_score" not in risk_context:
            missing.append("risk_score")
        
        return missing
    
    def _determine_action(
        self,
        mcda_scores: MCDAScores,
        wait_prob: WaitProbability,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any],
        available_units: Optional[List[str]]
    ) -> Tuple[ActionType, Optional[str], str]:
        """
        Determine the recommended action based on all inputs.
        
        Returns:
            Tuple of (action, target_unit, reasoning)
        """
        composite = mcda_scores.composite_score
        priority = mcda_scores.priority_level
        
        # Critical cases always escalate
        if priority == "CRITICAL":
            return (
                ActionType.ESCALATE,
                None,
                f"Critical priority ({composite:.0f}) requires immediate escalation. "
                f"Primary concern: {mcda_scores.dominant_factor}."
            )
        
        # Check if safe to wait
        if wait_prob.safe_to_wait and priority != "HIGH":
            wait_time = wait_prob.recommended_wait_time or 15
            return (
                ActionType.DELAY,
                None,
                f"Safe to wait {wait_time} minutes (probability: {wait_prob.probability:.0%}). "
                f"{wait_prob.benefit_if_waiting}"
            )
        
        # Determine if admission or transfer is appropriate
        current_location = patient_context.get("current_location", "ED")
        target_unit = patient_context.get("preferred_unit")
        
        if not target_unit and available_units:
            # Choose best available unit based on capacity
            target_unit = available_units[0] if available_units else None
        
        if capacity_context.get("capacity_score", 0) >= 50:
            # Good capacity, proceed with placement
            action = ActionType.ADMIT if current_location == "ED" else ActionType.TRANSFER
            return (
                action,
                target_unit,
                f"Recommending {action.value} to {target_unit or 'appropriate unit'} "
                f"(capacity score: {capacity_context.get('capacity_score', 0):.0f}). "
                f"Priority: {priority}."
            )
        else:
            # Low capacity, observe and wait
            return (
                ActionType.OBSERVE,
                None,
                f"Capacity constraints (score: {capacity_context.get('capacity_score', 0):.0f}). "
                f"Recommending observation until capacity improves."
            )
    
    def _generate_alternatives(
        self,
        primary_action: ActionType,
        mcda_scores: MCDAScores,
        wait_prob: WaitProbability
    ) -> List[Tuple[ActionType, str]]:
        """Generate alternative actions with reasoning."""
        alternatives = []
        
        # Always include opposite of primary
        if primary_action == ActionType.DELAY:
            alternatives.append((
                ActionType.ADMIT,
                "Proceed despite safe-to-wait if capacity is critical concern"
            ))
        elif primary_action in [ActionType.ADMIT, ActionType.TRANSFER]:
            if wait_prob.probability > 0.3:
                alternatives.append((
                    ActionType.DELAY,
                    f"Could wait up to {wait_prob.max_safe_wait} min if needed"
                ))
        
        # Escalation is always an alternative for high scores
        if mcda_scores.composite_score > 60 and primary_action != ActionType.ESCALATE:
            alternatives.append((
                ActionType.ESCALATE,
                "Escalate if situation worsens"
            ))
        
        # Observation as fallback
        if primary_action not in [ActionType.OBSERVE, ActionType.DELAY]:
            alternatives.append((
                ActionType.OBSERVE,
                "Continue monitoring if placement not immediately needed"
            ))
        
        return alternatives[:3]  # Limit to top 3 alternatives


# Convenience function for testing
def create_decision_engine(emergency_mode: bool = False) -> DecisionEngine:
    """Create a decision engine with appropriate weights."""
    if emergency_mode:
        weights = MCDAWeights.for_emergency()
    else:
        weights = MCDAWeights()
    
    return DecisionEngine(weights)
