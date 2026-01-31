"""
Capacity Intelligence Agent

Monitors hospital capacity including bed occupancy, staff ratios,
and predicts bed availability.

Exports:
- CapacityIntelligenceAgent: Main agent class
- CapacityAssessment: Output data model
- UnitType, BedState: Enums for unit and bed states
- create_demo_capacity_agent: Helper for testing
"""

from .models import (
    BedStatus,
    BedState,
    StaffWorkload,
    UnitCapacity,
    UnitType,
    CapacityAssessment,
)

from .trackers import (
    BedTracker,
    StaffTracker,
    AvailabilityPredictor,
    CapacityTrackingSystem,
)

from .agent import (
    CapacityIntelligenceAgent,
    create_demo_capacity_agent,
)

__all__ = [
    # Agent
    "CapacityIntelligenceAgent",
    "create_demo_capacity_agent",
    # Models
    "BedStatus",
    "BedState", 
    "StaffWorkload",
    "UnitCapacity",
    "UnitType",
    "CapacityAssessment",
    # Trackers
    "BedTracker",
    "StaffTracker",
    "AvailabilityPredictor",
    "CapacityTrackingSystem",
]
