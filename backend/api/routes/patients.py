from fastapi import APIRouter, HTTPException
from typing import List, Optional

from backend.core import state_manager
from backend.models import Patient, PatientSummary


router = APIRouter()


@router.get("/", response_model=List[PatientSummary])
async def list_patients():
    patients = await state_manager.get_all_patients()
    summaries = []
    for p in patients:
        risk = await state_manager.get_risk_assessment(p.patient_id)
        summaries.append(PatientSummary(
            patient_id=p.patient_id,
            name=p.name,
            age=p.age,
            current_location=p.current_location,
            chief_complaint=p.chief_complaint,
            arrival_time=p.arrival_time,
            risk_score=risk.risk_score if risk else None,
            risk_trajectory=risk.trajectory.value if risk else None,
        ))
    return summaries


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    patient = await state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/{patient_id}/vitals")
async def get_patient_vitals(patient_id: str, limit: int = 10):
    patient = await state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.vitals[-limit:]


@router.get("/{patient_id}/labs")
async def get_patient_labs(patient_id: str):
    patient = await state_manager.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.latest_labs


@router.get("/{patient_id}/risk")
async def get_patient_risk(patient_id: str):
    risk = await state_manager.get_risk_assessment(patient_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return risk
