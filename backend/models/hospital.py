from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class UnitType(str, Enum):
    ED = "ED"
    ICU = "ICU"
    WARD = "Ward"
    OR = "OR"


class BedStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class StaffRole(str, Enum):
    RN = "RN"
    MD = "MD"
    ATTENDING = "Attending"
    RESIDENT = "Resident"
    NP = "NP"
    PA = "PA"
    TECH = "Tech"


class Bed(BaseModel):
    bed_id: str
    unit: UnitType
    status: BedStatus
    patient_id: Optional[str] = None
    estimated_discharge: Optional[datetime] = None
    last_status_change: datetime


class Staff(BaseModel):
    staff_id: str
    name: str
    role: StaffRole
    unit: UnitType
    current_patients: List[str] = Field(default_factory=list)
    shift_start: datetime
    shift_end: datetime
    max_patients: int = 4

    @property
    def is_at_capacity(self) -> bool:
        return len(self.current_patients) >= self.max_patients

    @property
    def available_capacity(self) -> int:
        return max(0, self.max_patients - len(self.current_patients))


class UnitCapacity(BaseModel):
    unit: UnitType
    total_beds: int
    occupied_beds: int
    available_beds: int
    cleaning_beds: int = 0
    reserved_beds: int = 0
    total_staff: int
    staff_on_duty: int
    patients_per_nurse: float
    timestamp: datetime

    @property
    def occupancy_rate(self) -> float:
        if self.total_beds == 0:
            return 0.0
        return self.occupied_beds / self.total_beds

    @property
    def capacity_score(self) -> float:
        occupancy_penalty = self.occupancy_rate * 50
        staff_penalty = min(50, (self.patients_per_nurse / 6) * 50)
        return max(0, 100 - occupancy_penalty - staff_penalty)


class HospitalState(BaseModel):
    timestamp: datetime
    units: List[UnitCapacity] = Field(default_factory=list)
    beds: List[Bed] = Field(default_factory=list)
    staff: List[Staff] = Field(default_factory=list)

    def get_unit_capacity(self, unit: UnitType) -> Optional[UnitCapacity]:
        for u in self.units:
            if u.unit == unit:
                return u
        return None

    def get_available_beds(self, unit: UnitType) -> List[Bed]:
        return [b for b in self.beds if b.unit == unit and b.status == BedStatus.AVAILABLE]
