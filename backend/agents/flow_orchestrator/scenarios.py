"""
Flow Orchestrator Agent - Scenario Simulation

What-if scenario simulation for patient placement decisions.

Supports questions like:
- "What if we wait 15 minutes?"
- "What if we place in Ward instead of ICU?"
- "What happens if we prioritize this patient?"
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .models import ScenarioOutcome, PlacementOption, PlacementStatus
from backend.reasoning.mcda import MCDAScores, MCDAAnalyzer


class ScenarioSimulator:
    """
    Simulates what-if scenarios for patient placement.
    
    Answers questions about potential outcomes of different
    timing and placement decisions.
    """
    
    # Time scenarios to evaluate by default
    DEFAULT_WAIT_TIMES = [0, 15, 30, 60]  # minutes
    
    def __init__(self, mcda_analyzer: Optional[MCDAAnalyzer] = None):
        self.mcda_analyzer = mcda_analyzer or MCDAAnalyzer()
    
    def simulate_wait_scenario(
        self,
        current_capacity_score: float,
        patient_context: Dict[str, Any],
        wait_minutes: int,
        capacity_trend: str = "stable"  # improving, stable, declining
    ) -> ScenarioOutcome:
        """
        Simulate outcome of waiting a specified amount of time.
        
        Args:
            current_capacity_score: Current capacity (0-100)
            patient_context: Patient information
            wait_minutes: How long to wait
            capacity_trend: Expected capacity trend
        
        Returns:
            ScenarioOutcome with predicted results
        """
        scenario_id = f"wait_{wait_minutes}min"
        
        # Project capacity score based on trend
        if capacity_trend == "improving":
            improvement_rate = 0.5  # points per minute
            predicted_capacity = min(100, current_capacity_score + wait_minutes * improvement_rate)
            prob_better = 0.7
        elif capacity_trend == "declining":
            decline_rate = 0.3  # points per minute
            predicted_capacity = max(0, current_capacity_score - wait_minutes * decline_rate)
            prob_better = 0.3
        else:
            # Stable with slight improvement tendency
            predicted_capacity = min(100, current_capacity_score + wait_minutes * 0.15)
            prob_better = 0.5
        
        # Calculate risk level based on patient acuity and wait time
        acuity = patient_context.get("acuity_level", 3)
        risk = patient_context.get("risk_score", 50)
        
        if wait_minutes == 0:
            risk_level = "LOW"
        elif acuity >= 4 or risk >= 70:
            risk_level = "HIGH" if wait_minutes > 15 else "MEDIUM"
        elif acuity >= 3 or risk >= 50:
            risk_level = "MEDIUM" if wait_minutes > 30 else "LOW"
        else:
            risk_level = "LOW" if wait_minutes <= 60 else "MEDIUM"
        
        # Estimate additional wait for bed
        if predicted_capacity >= 70:
            additional_wait = 0
        elif predicted_capacity >= 50:
            additional_wait = 10
        elif predicted_capacity >= 30:
            additional_wait = 20
        else:
            additional_wait = 45
        
        # Generate benefits and risks
        benefits = []
        risks = []
        
        if capacity_trend == "improving" and wait_minutes > 0:
            benefits.append("Capacity expected to improve")
            if predicted_capacity > current_capacity_score + 10:
                benefits.append("Better bed options likely")
        
        if wait_minutes > 0:
            if patient_context.get("trajectory") == "deteriorating":
                risks.append("Patient condition may worsen")
                risk_level = "HIGH"
                prob_better = max(0.1, prob_better - 0.3)
            
            if patient_context.get("boarding_in_ed"):
                risks.append("Extended ED boarding")
            
            if acuity >= 4:
                risks.append("Delayed care for high-acuity patient")
        else:
            benefits.append("Immediate action")
            if current_capacity_score < 50:
                risks.append("Current capacity constraints")
        
        return ScenarioOutcome(
            scenario_id=scenario_id,
            description=f"Wait {wait_minutes} minutes before placement",
            wait_time_minutes=wait_minutes,
            predicted_capacity_score=predicted_capacity,
            predicted_wait_for_bed=additional_wait,
            risk_level=risk_level,
            expected_benefits=benefits,
            expected_risks=risks,
            probability_of_better_outcome=prob_better
        )
    
    def simulate_placement_scenarios(
        self,
        patient_context: Dict[str, Any],
        available_units: List[Dict[str, Any]],
        risk_context: Optional[Dict[str, Any]] = None
    ) -> List[PlacementOption]:
        """
        Simulate placement in different units.
        
        Args:
            patient_context: Patient information
            available_units: List of unit data with capacity info
            risk_context: Risk assessment data
        
        Returns:
            List of PlacementOptions ranked by viability
        """
        options = []
        
        for unit_data in available_units:
            unit_name = unit_data.get("unit", "Unknown")
            capacity_score = unit_data.get("capacity_score", 50)
            
            # Calculate MCDA scores for this placement
            capacity_context = {
                "capacity_score": capacity_score,
                "current_occupancy": unit_data.get("current_occupancy", 0.7),
                "staff_ratio": unit_data.get("staff_ratio", 1.0)
            }
            
            mcda_scores = self.mcda_analyzer.calculate_from_context(
                patient_context=patient_context,
                capacity_context=capacity_context,
                risk_context=risk_context
            )
            
            # Determine status
            if capacity_score >= 50:
                status = PlacementStatus.AVAILABLE
                wait_estimate = 0
            elif capacity_score >= 30:
                status = PlacementStatus.CONSTRAINED
                wait_estimate = 15
            elif unit_data.get("predicted_availability"):
                status = PlacementStatus.PENDING
                wait_estimate = 30
            else:
                status = PlacementStatus.UNAVAILABLE
                wait_estimate = 60
            
            # Check for constraints
            constraints = []
            if unit_data.get("current_occupancy", 0) > 0.9:
                constraints.append("High occupancy")
            if unit_data.get("staff_ratio", 0) > 5:
                constraints.append("Low staffing")
            if patient_context.get("isolation_required") and not unit_data.get("isolation_beds"):
                constraints.append("No isolation beds available")
            
            option = PlacementOption(
                option_id=f"place_{unit_name.lower()}",
                unit=unit_name,
                status=status,
                mcda_scores=mcda_scores,
                capacity_score=capacity_score,
                staff_ratio=unit_data.get("staff_ratio", 1.0),
                estimated_wait_minutes=wait_estimate,
                constraints=constraints
            )
            
            options.append(option)
        
        # Sort by viability score
        options.sort(key=lambda x: x.composite_viability_score, reverse=True)
        
        return options
    
    def run_timing_analysis(
        self,
        patient_context: Dict[str, Any],
        capacity_context: Dict[str, Any],
        wait_times: Optional[List[int]] = None
    ) -> List[ScenarioOutcome]:
        """
        Run analysis for multiple wait time scenarios.
        
        Returns scenarios sorted by probability of better outcome.
        """
        wait_times = wait_times or self.DEFAULT_WAIT_TIMES
        
        # Determine capacity trend
        predicted = capacity_context.get("predicted_availability")
        current_score = capacity_context.get("capacity_score", 50)
        
        if predicted:
            trend = "improving"
        elif current_score < 30:
            trend = "declining"
        else:
            trend = "stable"
        
        scenarios = []
        for wait in wait_times:
            scenario = self.simulate_wait_scenario(
                current_capacity_score=current_score,
                patient_context=patient_context,
                wait_minutes=wait,
                capacity_trend=trend
            )
            scenarios.append(scenario)
        
        return scenarios


class ScenarioComparator:
    """
    Compares scenarios and recommends the best option.
    """
    
    def compare_wait_scenarios(
        self,
        scenarios: List[ScenarioOutcome]
    ) -> Tuple[ScenarioOutcome, str]:
        """
        Compare wait scenarios and return the best one.
        
        Returns:
            Tuple of (best_scenario, explanation)
        """
        if not scenarios:
            return None, "No scenarios to compare"
        
        # Filter to favorable scenarios
        favorable = [s for s in scenarios if s.is_favorable]
        
        if favorable:
            # Among favorable, prefer shorter waits
            best = min(favorable, key=lambda s: s.wait_time_minutes)
            explanation = (
                f"Recommend waiting {best.wait_time_minutes} minutes. "
                f"Expected capacity: {best.predicted_capacity_score:.0f}. "
                f"{', '.join(best.expected_benefits)}"
            )
        else:
            # No favorable scenarios, choose immediate action
            best = scenarios[0]  # Assume first is wait=0
            immediate = next((s for s in scenarios if s.wait_time_minutes == 0), scenarios[0])
            best = immediate
            explanation = (
                f"Immediate action recommended (no favorable wait scenarios). "
                f"Risk level: {best.risk_level}."
            )
        
        return best, explanation
    
    def compare_placement_options(
        self,
        options: List[PlacementOption]
    ) -> Tuple[Optional[PlacementOption], List[PlacementOption], str]:
        """
        Compare placement options and return recommendation.
        
        Returns:
            Tuple of (best_option, alternatives, explanation)
        """
        if not options:
            return None, [], "No placement options available"
        
        viable = [opt for opt in options if opt.is_viable]
        
        if not viable:
            return (
                None, 
                options[:3],
                "No viable options currently. Consider waiting for capacity."
            )
        
        # Best is highest viability score
        best = max(viable, key=lambda x: x.composite_viability_score)
        alternatives = [opt for opt in viable if opt != best][:3]
        
        explanation = (
            f"Recommend placement in {best.unit} "
            f"(score: {best.composite_viability_score:.0f}). "
        )
        
        if best.constraints:
            explanation += f"Note: {', '.join(best.constraints)}. "
        
        if best.estimated_wait_minutes > 0:
            explanation += f"Estimated wait: {best.estimated_wait_minutes} minutes."
        
        return best, alternatives, explanation
