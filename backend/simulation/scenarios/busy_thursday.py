"""
'Busy Thursday' Scenario - High-stress ED simulation

Scenario Description:
- 15 ED patients over 2 hours
- 2 patients actively deteriorating (sepsis + respiratory)
- Mix of severities: 2 critical, 4 high, 6 moderate, 3 low
- ICU at 90% capacity (simulated context)
- Incoming trauma alert

This is the demo scenario for testing the Risk Monitor Agent.
"""
from backend.simulation.scenarios.base_scenario import BaseScenario
from backend.simulation.hospital_sim import HospitalSimulator
from backend.simulation.event_types import (
    DeteriorationPattern,
    ArrivalMode,
    SeverityLevel
)


class BusyThursdayScenario:
    """Busy ED evening with multiple deteriorating patients"""
    
    name = "Busy Thursday Evening"
    description = "15 ED patients, 2 deteriorating (sepsis + respiratory), ICU at 90% capacity, incoming trauma"
    duration_minutes = 120.0  # 2 hours
    
    @staticmethod
    def setup(simulator: HospitalSimulator) -> None:
        """Configure the busy Thursday scenario"""
        
        # === CRITICAL PATIENTS (2) ===
        
        # Patient 1: Sepsis - Progressive deterioration
        simulator.schedule_patient_arrival(
            delay_minutes=5,
            severity=SeverityLevel.CRITICAL,
            location="ED",
            deterioration=DeteriorationPattern.SEPSIS,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Sepsis - fever, hypotension"
        )
        
        # Patient 2: Severe respiratory distress
        simulator.schedule_patient_arrival(
            delay_minutes=12,
            severity=SeverityLevel.CRITICAL,
            location="ED",
            deterioration=DeteriorationPattern.RESPIRATORY,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Respiratory failure - COPD exacerbation"
        )
        
        # === HIGH SEVERITY PATIENTS (4) ===
        
        # Patient 3: Chest pain - potential MI
        simulator.schedule_patient_arrival(
            delay_minutes=8,
            severity=SeverityLevel.HIGH,
            location="ED",
            deterioration=DeteriorationPattern.GRADUAL_DECLINE,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Chest pain - crushing, radiating to jaw"
        )
        
        # Patient 4: Stroke symptoms
        simulator.schedule_patient_arrival(
            delay_minutes=25,
            severity=SeverityLevel.HIGH,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Stroke symptoms - sudden weakness, slurred speech"
        )
        
        # Patient 5: Trauma - MVA
        simulator.schedule_patient_arrival(
            delay_minutes=35,
            severity=SeverityLevel.HIGH,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.HELICOPTER,
            chief_complaint="Trauma - motor vehicle accident"
        )
        
        # Patient 6: Severe abdominal pain
        simulator.schedule_patient_arrival(
            delay_minutes=48,
            severity=SeverityLevel.HIGH,
            location="ED",
            deterioration=DeteriorationPattern.GRADUAL_DECLINE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Severe abdominal pain - possible appendicitis"
        )
        
        # === MODERATE SEVERITY PATIENTS (6) ===
        
        # Patient 7: Dehydration
        simulator.schedule_patient_arrival(
            delay_minutes=15,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Dehydration - vomiting, diarrhea"
        )
        
        # Patient 8: Asthma exacerbation
        simulator.schedule_patient_arrival(
            delay_minutes=22,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Asthma exacerbation"
        )
        
        # Patient 9: Diabetic - hyperglycemia
        simulator.schedule_patient_arrival(
            delay_minutes=30,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Diabetic emergency - high blood sugar"
        )
        
        # Patient 10: Fall injury
        simulator.schedule_patient_arrival(
            delay_minutes=42,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Fall - possible fracture"
        )
        
        # Patient 11: Syncope
        simulator.schedule_patient_arrival(
            delay_minutes=55,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.AMBULANCE,
            chief_complaint="Syncope - loss of consciousness"
        )
        
        # Patient 12: Migraine
        simulator.schedule_patient_arrival(
            delay_minutes=68,
            severity=SeverityLevel.MODERATE,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Severe migraine"
        )
        
        # === LOW SEVERITY PATIENTS (3) ===
        
        # Patient 13: Minor laceration
        simulator.schedule_patient_arrival(
            delay_minutes=40,
            severity=SeverityLevel.LOW,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Laceration - needs stitches"
        )
        
        # Patient 14: Sprain
        simulator.schedule_patient_arrival(
            delay_minutes=60,
            severity=SeverityLevel.LOW,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="Ankle sprain"
        )
        
        # Patient 15: UTI symptoms
        simulator.schedule_patient_arrival(
            delay_minutes=75,
            severity=SeverityLevel.LOW,
            location="ED",
            deterioration=DeteriorationPattern.STABLE,
            arrival_mode=ArrivalMode.WALK_IN,
            chief_complaint="UTI symptoms"
        )
