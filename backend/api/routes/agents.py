from fastapi import APIRouter
from typing import Dict, Any


router = APIRouter()


def get_orchestrator():
    from backend.api.main import orchestrator
    return orchestrator


@router.get("/status")
async def get_agents_status() -> Dict[str, Any]:
    return get_orchestrator().get_agent_status()


@router.get("/list")
async def list_agents():
    return {"agents": get_orchestrator().list_agents()}


@router.post("/run/{agent_name}")
async def run_agent(agent_name: str, patient_id: str):
    context = {"patient_id": patient_id}
    result = await get_orchestrator().run_single_agent(agent_name, context)
    if not result:
        return {"error": f"Agent {agent_name} not found or failed"}
    return result


@router.post("/pipeline/{patient_id}")
async def run_pipeline(patient_id: str):
    results = await get_orchestrator().run_pipeline(patient_id)
    return {
        "patient_id": patient_id,
        "results": {k: v.model_dump() for k, v in results.items()},
    }


@router.post("/process-all")
async def process_all_patients():
    results = await get_orchestrator().process_all_patients()
    return {
        "patients_processed": len(results),
        "patient_ids": list(results.keys()),
    }
