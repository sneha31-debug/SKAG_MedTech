from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.core import state_manager, event_bus
from backend.models import EventType


router = APIRouter()


class SimulationControl(BaseModel):
    speed: Optional[float] = 1.0


@router.get("/status")
async def get_simulation_status():
    return {
        "running": state_manager.is_simulation_running(),
        "current_time": state_manager.get_simulation_time().isoformat(),
    }


@router.post("/start")
async def start_simulation(control: SimulationControl = SimulationControl()):
    if state_manager.is_simulation_running():
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    state_manager.set_simulation_running(True)
    await event_bus.publish(EventType.SIMULATION_START.value, {"speed": control.speed})
    return {"status": "started", "speed": control.speed}


@router.post("/stop")
async def stop_simulation():
    if not state_manager.is_simulation_running():
        raise HTTPException(status_code=400, detail="Simulation not running")
    
    state_manager.set_simulation_running(False)
    await event_bus.publish(EventType.SIMULATION_STOP.value, {})
    return {"status": "stopped"}


@router.post("/reset")
async def reset_simulation():
    state_manager.set_simulation_running(False)
    await state_manager.clear()
    await event_bus.publish(EventType.SIMULATION_RESET.value, {})
    return {"status": "reset"}


@router.get("/hospital")
async def get_hospital_state():
    state = await state_manager.get_hospital_state()
    if not state:
        return {"message": "No hospital state available"}
    return state


@router.get("/capacity/{unit}")
async def get_unit_capacity(unit: str):
    capacity = await state_manager.get_capacity_assessment(unit)
    if not capacity:
        raise HTTPException(status_code=404, detail=f"Capacity for {unit} not found")
    return capacity
