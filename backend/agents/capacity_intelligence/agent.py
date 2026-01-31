

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional

from .models import CapacityAssessment, UnitType, UnitCapacity
from .trackers import CapacityTrackingSystem


class BaseAgent(ABC):
    
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

class CapacityIntelligenceAgent(BaseAgent):
    """
    Capacity Intelligence Agent - tracks and reports hospital capacity.
    
    Responsibilities:
    - Monitor bed occupancy across all units
    - Track staff-to-patient ratios
    - Predict when beds will become available
    - Produce CapacityAssessment for each unit
    
    Usage:
        agent = CapacityIntelligenceAgent()
        agent.initialize_demo_data()  # For testing
        
        # Async usage (with BaseAgent interface)
        assessment = await agent.execute({"unit": "ICU"})
        
        # Sync usage (direct method calls)
        assessment = agent.get_unit_assessment("ICU")
    """
    
    def __init__(self, event_bus=None, state_manager=None):
        super().__init__(event_bus, state_manager)
        self.tracking_system = CapacityTrackingSystem()
        self._initialized = False
    
    def initialize_demo_data(self) -> None:
        """Initialize with demo hospital data for testing."""
        self.tracking_system.initialize_demo_data()
        self._initialized = True
    
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather current capacity data.
        
        Args:
            context: May contain "unit" to observe a specific unit,
                    or observe all units if not specified.
        
        Returns:
            dict with capacity observations for requested unit(s)
        """
        if not self._initialized:
            self.initialize_demo_data()
        
        unit_name = context.get("unit")
        
        if unit_name:
            # Observe specific unit
            try:
                unit = UnitType(unit_name) if isinstance(unit_name, str) else unit_name
                capacity = self.tracking_system.bed_tracker.get_unit_capacity(unit)
                staff_metrics = self.tracking_system.staff_tracker.get_unit_staff_metrics(unit)
                
                return {
                    "unit": unit_name,
                    "bed_capacity": capacity.to_dict(),
                    "staff_metrics": staff_metrics,
                    "timestamp": datetime.now().isoformat()
                }
            except ValueError:
                return {"error": f"Unknown unit: {unit_name}"}
        else:
            # Observe all units
            observations = {}
            for unit in UnitType:
                capacity = self.tracking_system.bed_tracker.get_unit_capacity(unit)
                staff_metrics = self.tracking_system.staff_tracker.get_unit_staff_metrics(unit)
                observations[unit.value] = {
                    "bed_capacity": capacity.to_dict(),
                    "staff_metrics": staff_metrics
                }
            
            observations["timestamp"] = datetime.now().isoformat()
            return observations
    
    async def decide(self, observations: Dict[str, Any]) -> Dict[str, CapacityAssessment]:
        """
        Produce CapacityAssessment outputs based on observations.
        
        Returns:
            dict mapping unit names to CapacityAssessment objects
        """
        assessments = {}
        
        # Check if single unit observation
        if "unit" in observations and "bed_capacity" in observations:
            unit_name = observations["unit"]
            unit = UnitType(unit_name) if isinstance(unit_name, str) else unit_name
            assessment = self.tracking_system.get_unit_assessment(unit)
            assessments[unit_name] = assessment
        else:
            # Multiple units
            for unit in UnitType:
                if unit.value in observations:
                    assessment = self.tracking_system.get_unit_assessment(unit)
                    assessments[unit.value] = assessment
        
        return assessments
    
    # ========================================================================
    # Synchronous convenience methods for direct usage
    # ========================================================================
    
    def get_unit_assessment(self, unit: str) -> CapacityAssessment:
        """
        Get capacity assessment for a specific unit (sync method).
        
        Args:
            unit: Unit name (ICU, Ward, ED, etc.)
        
        Returns:
            CapacityAssessment for the unit
        """
        if not self._initialized:
            self.initialize_demo_data()
        
        unit_type = UnitType(unit)
        return self.tracking_system.get_unit_assessment(unit_type)
    
    def get_all_assessments(self) -> Dict[str, CapacityAssessment]:
        """
        Get capacity assessments for all units (sync method).
        
        Returns:
            dict mapping unit names to CapacityAssessment objects
        """
        if not self._initialized:
            self.initialize_demo_data()
        
        return self.tracking_system.get_all_assessments()
    
    def get_unit_occupancy(self, unit: str) -> float:
        """Get current occupancy rate for a unit."""
        assessment = self.get_unit_assessment(unit)
        return assessment.current_occupancy
    
    def get_available_bed_count(self, unit: Optional[str] = None) -> int:
        """Get count of available beds."""
        if not self._initialized:
            self.initialize_demo_data()
        
        if unit:
            assessment = self.get_unit_assessment(unit)
            return assessment.available_bed_count
        else:
            total = 0
            for assessment in self.get_all_assessments().values():
                total += assessment.available_bed_count
            return total
    
    def find_best_unit_for_admission(self, 
                                      preferred_units: Optional[List[str]] = None
                                      ) -> Optional[str]:
        """
        Find the best unit for a new admission based on capacity.
        
        Args:
            preferred_units: List of preferred unit types, or None for any
        
        Returns:
            Unit name with highest capacity score, or None if all full
        """
        assessments = self.get_all_assessments()
        
        candidates = []
        for unit_name, assessment in assessments.items():
            if preferred_units and unit_name not in preferred_units:
                continue
            if assessment.available_bed_count > 0:
                candidates.append((unit_name, assessment.capacity_score))
        
        if not candidates:
            return None
        
        # Return unit with highest capacity score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current capacity status across all units.
        
        Returns:
            Summary dict for debugging and monitoring
        """
        if not self._initialized:
            self.initialize_demo_data()
        
        assessments = self.get_all_assessments()
        
        total_beds = sum(a.total_bed_count for a in assessments.values())
        available_beds = sum(a.available_bed_count for a in assessments.values())
        
        units_summary = {}
        for unit_name, assessment in assessments.items():
            units_summary[unit_name] = {
                "occupancy": f"{assessment.current_occupancy:.1%}",
                "available": assessment.available_bed_count,
                "total": assessment.total_bed_count,
                "capacity_score": f"{assessment.capacity_score:.1f}",
                "bottleneck": assessment.bottleneck_reason
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hospital_total_beds": total_beds,
            "hospital_available_beds": available_beds,
            "hospital_occupancy": f"{(total_beds - available_beds) / total_beds:.1%}" if total_beds > 0 else "N/A",
            "units": units_summary
        }


# Convenience function for quick testing
def create_demo_capacity_agent() -> CapacityIntelligenceAgent:
    """Create a capacity agent with demo data for testing."""
    agent = CapacityIntelligenceAgent()
    agent.initialize_demo_data()
    return agent
