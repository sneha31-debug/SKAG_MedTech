from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Location(str, Enum):
    ED = "ED"
    ICU = "ICU"
    WARD = "Ward"
    ED_OBS = "ED_Obs"
    OR = "OR"
    DISCHARGE = "Discharge"


class VitalSigns(BaseModel):
    heart_rate: int = Field(..., ge=0, le=300)
    blood_pressure_systolic: int = Field(..., ge=0, le=300)
    blood_pressure_diastolic: int = Field(..., ge=0, le=200)
    oxygen_saturation: float = Field(..., ge=0, le=100)
    respiratory_rate: int = Field(..., ge=0, le=60)
    temperature: float = Field(..., ge=30.0, le=45.0)
    glasgow_coma_scale: int = Field(..., ge=3, le=15)
    timestamp: datetime


class LabResult(BaseModel):
    test_name: str
    value: float
    unit: str
    timestamp: datetime
    normal_range_low: float
    normal_range_high: float

    @property
    def is_abnormal(self) -> bool:
        return self.value < self.normal_range_low or self.value > self.normal_range_high


class Patient(BaseModel):
    patient_id: str
    name: str
    age: int = Field(..., ge=0, le=150)
    gender: Gender
    chief_complaint: str
    arrival_time: datetime
    current_location: Location
    vitals: List[VitalSigns] = Field(default_factory=list)
    labs: List[LabResult] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    @property
    def latest_vitals(self) -> Optional[VitalSigns]:
        if not self.vitals:
            return None
        return max(self.vitals, key=lambda v: v.timestamp)

    @property
    def latest_labs(self) -> dict[str, LabResult]:
        if not self.labs:
            return {}
        latest = {}
        for lab in sorted(self.labs, key=lambda l: l.timestamp):
            latest[lab.test_name] = lab
        return latest


class PatientSummary(BaseModel):
    patient_id: str
    name: str
    age: int
    current_location: Location
    chief_complaint: str
    arrival_time: datetime
    risk_score: Optional[float] = None
    risk_trajectory: Optional[str] = None
