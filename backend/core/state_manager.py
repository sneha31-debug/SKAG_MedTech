from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.models import Patient, HospitalState, Decision, RiskAssessment, CapacityAssessment, FlowRecommendation


class StateManager:
    
    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        self._hospital_state: Optional[HospitalState] = None
        self._decisions: List[Decision] = []
        self._agent_outputs: Dict[str, Dict[str, Any]] = {}
        self._simulation_time: datetime = datetime.utcnow()
        self._simulation_running: bool = False

    async def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self._patients.get(patient_id)

    async def get_all_patients(self) -> List[Patient]:
        return list(self._patients.values())

    async def update_patient(self, patient: Patient) -> None:
        self._patients[patient.patient_id] = patient

    async def remove_patient(self, patient_id: str) -> None:
        if patient_id in self._patients:
            del self._patients[patient_id]

    async def get_hospital_state(self) -> Optional[HospitalState]:
        return self._hospital_state

    async def update_hospital_state(self, state: HospitalState) -> None:
        self._hospital_state = state

    async def store_decision(self, decision: Decision) -> None:
        self._decisions.append(decision)
        if len(self._decisions) > 10000:
            self._decisions = self._decisions[-10000:]

    async def get_decisions(self, patient_id: str = None, limit: int = 100) -> List[Decision]:
        if patient_id:
            filtered = [d for d in self._decisions if d.patient_id == patient_id]
        else:
            filtered = self._decisions
        return filtered[-limit:]

    async def store_agent_output(self, agent_name: str, patient_id: str, output: Any) -> None:
        if agent_name not in self._agent_outputs:
            self._agent_outputs[agent_name] = {}
        self._agent_outputs[agent_name][patient_id] = output

    async def get_agent_output(self, agent_name: str, patient_id: str) -> Optional[Any]:
        return self._agent_outputs.get(agent_name, {}).get(patient_id)

    async def get_risk_assessment(self, patient_id: str) -> Optional[RiskAssessment]:
        return await self.get_agent_output("RiskMonitorAgent", patient_id)

    async def get_capacity_assessment(self, unit: str) -> Optional[CapacityAssessment]:
        return await self.get_agent_output("CapacityIntelligenceAgent", unit)

    async def get_flow_recommendation(self, patient_id: str) -> Optional[FlowRecommendation]:
        return await self.get_agent_output("FlowOrchestratorAgent", patient_id)

    def set_simulation_time(self, time: datetime) -> None:
        self._simulation_time = time

    def get_simulation_time(self) -> datetime:
        return self._simulation_time

    def set_simulation_running(self, running: bool) -> None:
        self._simulation_running = running

    def is_simulation_running(self) -> bool:
        return self._simulation_running

    async def clear(self) -> None:
        self._patients.clear()
        self._hospital_state = None
        self._decisions.clear()
        self._agent_outputs.clear()
        self._simulation_time = datetime.utcnow()
        self._simulation_running = False


state_manager = StateManager()
