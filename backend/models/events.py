from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import uuid


class EventType(str, Enum):
    PATIENT_ARRIVAL = "patient.arrival"
    PATIENT_DISCHARGE = "patient.discharge"
    PATIENT_TRANSFER = "patient.transfer"
    VITALS_UPDATE = "vitals.update"
    LAB_RESULT = "lab.result"
    BED_STATUS_CHANGE = "bed.status_change"
    STAFF_SHIFT_START = "staff.shift_start"
    STAFF_SHIFT_END = "staff.shift_end"
    RISK_CALCULATED = "risk_monitor.risk_calculated"
    CAPACITY_UPDATED = "capacity_intelligence.capacity_updated"
    FLOW_RECOMMENDATION = "flow_orchestrator.recommendation_ready"
    ESCALATION_DECISION = "escalation_decision.decision_made"
    SIMULATION_TICK = "simulation.tick"
    SIMULATION_START = "simulation.start"
    SIMULATION_STOP = "simulation.stop"
    SIMULATION_RESET = "simulation.reset"


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    patient_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class PatientArrivalEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.PATIENT_ARRIVAL
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "simulation"
    patient_id: str
    name: str
    age: int
    gender: str
    chief_complaint: str
    initial_location: str


class VitalsUpdateEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.VITALS_UPDATE
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "simulation"
    patient_id: str
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    oxygen_saturation: float
    respiratory_rate: int
    temperature: float
    glasgow_coma_scale: int


class LabResultEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.LAB_RESULT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "simulation"
    patient_id: str
    test_name: str
    value: float
    unit: str
    normal_range_low: float
    normal_range_high: float


class BedStatusChangeEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.BED_STATUS_CHANGE
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "simulation"
    bed_id: str
    unit: str
    old_status: str
    new_status: str
    patient_id: Optional[str] = None
