"""
Simulation-specific event types for hospital simulation.
Uses the base Event types from models.events and extends with simulation-specific classes.
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class DeteriorationPattern(str, Enum):
    """Patterns of patient deterioration"""
    STABLE = "stable"
    GRADUAL_DECLINE = "gradual_decline"
    RAPID_DECLINE = "rapid_decline"
    SEPSIS = "sepsis"
    CARDIAC = "cardiac"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"


class ArrivalMode(str, Enum):
    """How patient arrived at hospital"""
    WALK_IN = "walk_in"
    AMBULANCE = "ambulance"
    TRANSFER = "transfer"
    HELICOPTER = "helicopter"


class SeverityLevel(str, Enum):
    """Initial severity assessment"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SimulationEvent(BaseModel):
    """Base class for all simulation events"""
    event_id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    sim_time: float  # Simulation time in minutes
    timestamp: datetime
    patient_id: Optional[str] = None


class PatientArrivalSimEvent(SimulationEvent):
    """Patient arrives at hospital"""
    arrival_mode: ArrivalMode
    severity: SeverityLevel
    chief_complaint: str
    initial_vitals: dict
    deterioration_pattern: DeteriorationPattern = DeteriorationPattern.STABLE


class VitalsUpdateSimEvent(SimulationEvent):
    """Periodic vital signs update"""
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    oxygen_saturation: float
    respiratory_rate: int
    temperature: float
    glasgow_coma_scale: int
    deterioration_indicator: Optional[str] = None


class LabResultSimEvent(SimulationEvent):
    """Lab test result becomes available"""
    test_name: str
    value: float
    unit: str
    normal_range_low: float
    normal_range_high: float
    critical: bool = False


class BedChangeSimEvent(SimulationEvent):
    """Patient moved to different bed/unit"""
    from_unit: str
    to_unit: str
    from_bed: Optional[str]
    to_bed: str
    reason: str


class StaffShiftSimEvent(SimulationEvent):
    """Staff shift change"""
    staff_id: str
    role: str
    unit: str
    shift_type: str  # "start" or "end"


class DeteriorationSimEvent(SimulationEvent):
    """Patient condition deteriorating"""
    deterioration_type: DeteriorationPattern
    severity_change: str  # e.g., "moderate -> critical"
    trigger_vitals: dict
    needs_escalation: bool = True
