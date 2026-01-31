"""
Synthetic data generator for hospital simulation.
Generates realistic patient profiles and vital signs.
"""
import random
from datetime import datetime, timedelta
from typing import List
from backend.models.patient import Patient, VitalSigns, PatientStatus, AcuityLevel, RiskFactors
from backend.simulation.event_types import (
    DeteriorationPattern,
    SeverityLevel
)


class DataGenerator:
    """Generates realistic hospital data for simulation"""
    
    CHIEF_COMPLAINTS = [
        "Chest pain",
        "Shortness of breath",
        "Abdominal pain",
        "Fever",
        "Headache",
        "Trauma - MVA",
        "Fall injury",
        "Altered mental status",
        "Seizure",
        "Syncope",
        "Severe bleeding",
        "Sepsis",
        "Stroke symptoms",
        "Diabetic emergency"
    ]
    
    FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", 
                   "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson"]
    
    COMORBIDITIES = [
        "Hypertension",
        "Diabetes Type 2",
        "COPD",
        "Asthma",
        "CAD",
        "CHF",
        "Atrial fibrillation",
        "CKD",
        "Previous MI",
        "Stroke history"
    ]
    
    @staticmethod
    def generate_patient_id() -> str:
        """Generate unique patient ID"""
        return f"PT{random.randint(10000, 99999)}"
    
    @staticmethod
    def generate_name() -> str:
        """Generate random patient name"""
        first = random.choice(DataGenerator.FIRST_NAMES)
        last = random.choice(DataGenerator.LAST_NAMES)
        return f"{first} {last}"
    
    @staticmethod
    def generate_age(severity: SeverityLevel) -> int:
        """Generate age based on severity (older patients tend to be sicker)"""
        if severity == SeverityLevel.CRITICAL:
            return random.randint(65, 90)
        elif severity == SeverityLevel.HIGH:
            return random.randint(50, 80)
        elif severity == SeverityLevel.MODERATE:
            return random.randint(35, 70)
        else:
            return random.randint(18, 60)
    
    @staticmethod
    def severity_to_acuity(severity: SeverityLevel) -> AcuityLevel:
        """Map severity level to acuity level"""
        mapping = {
            SeverityLevel.CRITICAL: AcuityLevel.RESUSCITATION,
            SeverityLevel.HIGH: AcuityLevel.EMERGENT,
            SeverityLevel.MODERATE: AcuityLevel.URGENT,
            SeverityLevel.LOW: AcuityLevel.LESS_URGENT
        }
        return mapping.get(severity, AcuityLevel.URGENT)
    
    @staticmethod
    def generate_vitals(
        severity: SeverityLevel,
        deterioration: DeteriorationPattern = DeteriorationPattern.STABLE,
        time_offset: int = 0
    ) -> VitalSigns:
        """Generate vital signs based on patient severity and deterioration pattern"""
        
        # Base normal vitals
        base = {
            "heart_rate": 75,
            "systolic": 120,
            "diastolic": 80,
            "spo2": 98.0,
            "respiratory_rate": 16,
            "temperature": 37.0
        }
        
        # Adjust based on severity
        if severity == SeverityLevel.CRITICAL:
            base["heart_rate"] = random.randint(110, 150)
            base["systolic"] = random.randint(80, 100)
            base["spo2"] = random.uniform(85, 92)
            base["respiratory_rate"] = random.randint(25, 35)
        elif severity == SeverityLevel.HIGH:
            base["heart_rate"] = random.randint(95, 120)
            base["systolic"] = random.randint(90, 110)
            base["spo2"] = random.uniform(90, 95)
            base["respiratory_rate"] = random.randint(20, 28)
        elif severity == SeverityLevel.MODERATE:
            base["heart_rate"] = random.randint(80, 100)
            base["systolic"] = random.randint(100, 130)
            base["spo2"] = random.uniform(94, 97)
            base["respiratory_rate"] = random.randint(18, 24)
        
        # Apply deterioration pattern over time
        if deterioration == DeteriorationPattern.RAPID_DECLINE:
            decline_factor = min(time_offset * 0.15, 1.0)
            base["heart_rate"] = int(base["heart_rate"] + (40 * decline_factor))
            base["spo2"] = max(75, base["spo2"] - (15 * decline_factor))
        elif deterioration == DeteriorationPattern.GRADUAL_DECLINE:
            decline_factor = min(time_offset * 0.05, 1.0)
            base["heart_rate"] = int(base["heart_rate"] + (20 * decline_factor))
            base["spo2"] = max(85, base["spo2"] - (8 * decline_factor))
        elif deterioration == DeteriorationPattern.SEPSIS:
            base["heart_rate"] = random.randint(120, 160)
            base["temperature"] = random.uniform(38.5, 40.0)
            base["respiratory_rate"] = random.randint(28, 40)
            base["systolic"] = random.randint(70, 90)
        elif deterioration == DeteriorationPattern.RESPIRATORY:
            base["spo2"] = random.uniform(80, 88)
            base["respiratory_rate"] = random.randint(30, 45)
            base["heart_rate"] = random.randint(110, 140)
        
        return VitalSigns(
            heart_rate=base["heart_rate"],
            systolic_bp=base["systolic"],
            diastolic_bp=base["diastolic"],
            spo2=round(base["spo2"], 1),
            respiratory_rate=base["respiratory_rate"],
            temperature=round(base["temperature"], 1),
            measured_at=datetime.now() + timedelta(minutes=time_offset)
        )
    
    @staticmethod
    def generate_patient(
        severity: SeverityLevel,
        location: str = "ED",
        deterioration_pattern: DeteriorationPattern = DeteriorationPattern.STABLE,
        chief_complaint: str = None
    ) -> Patient:
        """Generate a complete patient with realistic data"""
        
        patient_id = DataGenerator.generate_patient_id()
        age = DataGenerator.generate_age(severity)
        
        # Generate medical history based on age
        comorbidities = random.sample(
            DataGenerator.COMORBIDITIES,
            k=random.randint(0, 2) if age < 50 else random.randint(2, 4)
        )
        
        # Generate initial vitals
        initial_vitals = DataGenerator.generate_vitals(severity, deterioration_pattern, 0)
        
        # Generate risk factors based on deterioration
        risk_factors = RiskFactors()
        if deterioration_pattern == DeteriorationPattern.SEPSIS:
            risk_factors.sepsis_probability = random.uniform(0.6, 0.9)
        elif deterioration_pattern == DeteriorationPattern.RESPIRATORY:
            risk_factors.respiratory_risk = random.uniform(0.6, 0.9)
        elif deterioration_pattern == DeteriorationPattern.CARDIAC:
            risk_factors.cardiac_risk = random.uniform(0.6, 0.9)
        
        if deterioration_pattern != DeteriorationPattern.STABLE:
            risk_factors.deterioration_trend = random.uniform(0.5, 1.0)
        
        return Patient(
            id=patient_id,
            name=DataGenerator.generate_name(),
            age=age,
            gender=random.choice(["M", "F", "O"]),
            chief_complaint=chief_complaint or random.choice(DataGenerator.CHIEF_COMPLAINTS),
            admission_time=datetime.now(),
            current_location=location,
            vitals=initial_vitals,
            comorbidities=comorbidities,
            acuity_level=DataGenerator.severity_to_acuity(severity),
            status=PatientStatus.WAITING,
            risk_factors=risk_factors,
            notes=[]
        )
