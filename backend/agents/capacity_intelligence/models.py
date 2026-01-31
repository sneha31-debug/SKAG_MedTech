"""
Capacity Intelligence Agent - Data Models

Models for tracking hospital capacity including bed status, staff workload,
and unit-level capacity assessments.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


class BedState(str, Enum):
    """Possible states for a hospital bed."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class UnitType(str, Enum):
    """Types of hospital units."""
    ICU = "ICU"
    WARD = "Ward"
    ED = "ED"
    OR = "OR"  # Operating Room
    PACU = "PACU"  # Post-Anesthesia Care Unit


@dataclass
class BedStatus:
    """Status of an individual hospital bed."""
    bed_id: str
    unit: UnitType
    state: BedState
    patient_id: Optional[str] = None
    assigned_nurse_id: Optional[str] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    estimated_available_at: Optional[datetime] = None
    
    @property
    def is_available(self) -> bool:
        return self.state == BedState.AVAILABLE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bed_id": self.bed_id,
            "unit": self.unit.value,
            "state": self.state.value,
            "patient_id": self.patient_id,
            "assigned_nurse_id": self.assigned_nurse_id,
            "last_state_change": self.last_state_change.isoformat(),
            "estimated_available_at": self.estimated_available_at.isoformat() if self.estimated_available_at else None
        }


@dataclass 
class StaffWorkload:
    """Workload metrics for a staff member."""
    staff_id: str
    name: str
    role: str  # nurse, doctor, tech
    unit: UnitType
    assigned_patients: List[str] = field(default_factory=list)
    current_patient_count: int = 0
    max_patient_capacity: int = 4  # Configurable based on role/unit
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    
    @property
    def workload_ratio(self) -> float:
        """Calculate workload as a percentage (0-1)."""
        if self.max_patient_capacity == 0:
            return 1.0
        return min(self.current_patient_count / self.max_patient_capacity, 1.0)
    
    @property
    def available_capacity(self) -> int:
        """Number of additional patients this staff member can take."""
        return max(0, self.max_patient_capacity - self.current_patient_count)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "staff_id": self.staff_id,
            "name": self.name,
            "role": self.role,
            "unit": self.unit.value,
            "assigned_patients": self.assigned_patients,
            "current_patient_count": self.current_patient_count,
            "max_patient_capacity": self.max_patient_capacity,
            "workload_ratio": self.workload_ratio,
            "available_capacity": self.available_capacity
        }


@dataclass
class UnitCapacity:
    """Aggregate capacity metrics for a hospital unit."""
    unit: UnitType
    total_beds: int
    occupied_beds: int
    available_beds: int
    reserved_beds: int = 0
    cleaning_beds: int = 0
    staff_on_duty: int = 0
    target_staff_ratio: float = 0.25  # Target patients per staff member
    
    @property
    def occupancy_rate(self) -> float:
        """Bed occupancy as a percentage (0-1)."""
        if self.total_beds == 0:
            return 0.0
        return self.occupied_beds / self.total_beds
    
    @property
    def effective_availability(self) -> int:
        """Beds actually available for immediate use."""
        return self.available_beds - self.reserved_beds
    
    @property
    def current_staff_ratio(self) -> float:
        """Current patients per staff member."""
        if self.staff_on_duty == 0:
            return float('inf')
        return self.occupied_beds / self.staff_on_duty
    
    @property
    def staff_adequacy(self) -> float:
        """How adequate staffing is (>1 = overstaffed, <1 = understaffed)."""
        if self.target_staff_ratio == 0:
            return 1.0
        return self.target_staff_ratio / self.current_staff_ratio if self.current_staff_ratio > 0 else 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit.value,
            "total_beds": self.total_beds,
            "occupied_beds": self.occupied_beds,
            "available_beds": self.available_beds,
            "reserved_beds": self.reserved_beds,
            "cleaning_beds": self.cleaning_beds,
            "staff_on_duty": self.staff_on_duty,
            "occupancy_rate": self.occupancy_rate,
            "effective_availability": self.effective_availability,
            "current_staff_ratio": self.current_staff_ratio,
            "staff_adequacy": self.staff_adequacy
        }


@dataclass
class CapacityAssessment:
    """
    Output from the Capacity Intelligence Agent.
    
    This is the primary data contract for capacity information,
    consumed by the Flow Orchestrator and Escalation agents.
    """
    unit: str  # ICU, Ward, ED
    current_occupancy: float  # Occupancy rate (0-1)
    staff_ratio: float  # Patients per staff member
    capacity_score: float  # Overall capacity score (0-100, higher = more available)
    predicted_availability: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.85  # Confidence in the assessment
    
    # Additional context
    available_bed_count: int = 0
    total_bed_count: int = 0
    staff_on_duty: int = 0
    bottleneck_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit,
            "current_occupancy": self.current_occupancy,
            "staff_ratio": self.staff_ratio,
            "capacity_score": self.capacity_score,
            "predicted_availability": self.predicted_availability.isoformat() if self.predicted_availability else None,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "available_bed_count": self.available_bed_count,
            "total_bed_count": self.total_bed_count,
            "staff_on_duty": self.staff_on_duty,
            "bottleneck_reason": self.bottleneck_reason
        }
    
    @classmethod
    def from_unit_capacity(cls, unit_cap: UnitCapacity, predicted_availability: Optional[datetime] = None) -> "CapacityAssessment":
        """Create a CapacityAssessment from UnitCapacity data."""
        # Calculate capacity score (0-100)
        # Higher score = more capacity available
        bed_score = (1 - unit_cap.occupancy_rate) * 50  # Up to 50 points for bed availability
        staff_score = min(unit_cap.staff_adequacy, 1.5) / 1.5 * 50  # Up to 50 points for staffing
        capacity_score = bed_score + staff_score
        
        # Determine bottleneck
        bottleneck = None
        if unit_cap.occupancy_rate > 0.9:
            bottleneck = "High bed occupancy"
        elif unit_cap.staff_adequacy < 0.7:
            bottleneck = "Staff shortage"
        
        return cls(
            unit=unit_cap.unit.value,
            current_occupancy=unit_cap.occupancy_rate,
            staff_ratio=unit_cap.current_staff_ratio,
            capacity_score=capacity_score,
            predicted_availability=predicted_availability,
            available_bed_count=unit_cap.available_beds,
            total_bed_count=unit_cap.total_beds,
            staff_on_duty=unit_cap.staff_on_duty,
            bottleneck_reason=bottleneck
        )
