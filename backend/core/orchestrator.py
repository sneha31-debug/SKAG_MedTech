from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.core.event_bus import EventBus
from backend.core.state_manager import StateManager
from backend.agents.base_agent import BaseAgent
from backend.models import Patient, Decision, EventType


class Orchestrator:
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state = state_manager
        self._agents: Dict[str, BaseAgent] = {}
        self._pipeline_order: List[str] = [
            "RiskMonitorAgent",
            "CapacityIntelligenceAgent",
            "FlowOrchestratorAgent",
            "EscalationDecisionAgent",
        ]

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def unregister_agent(self, agent_name: str) -> None:
        if agent_name in self._agents:
            del self._agents[agent_name]

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_name)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    async def run_pipeline(self, patient_id: str) -> Dict[str, Decision]:
        context = {
            "patient_id": patient_id,
            "timestamp": self.state.get_simulation_time(),
        }
        
        results = {}
        
        for agent_name in self._pipeline_order:
            agent = self._agents.get(agent_name)
            if agent:
                try:
                    decision = await agent.execute(context)
                    results[agent_name] = decision
                    await self.state.store_decision(decision)
                except Exception:
                    pass
        
        return results

    async def run_single_agent(self, agent_name: str, context: Dict[str, Any]) -> Optional[Decision]:
        agent = self._agents.get(agent_name)
        if not agent:
            return None
        
        try:
            decision = await agent.execute(context)
            await self.state.store_decision(decision)
            return decision
        except Exception:
            return None

    async def process_patient_event(self, patient_id: str) -> None:
        await self.run_pipeline(patient_id)

    async def process_all_patients(self) -> Dict[str, Dict[str, Decision]]:
        patients = await self.state.get_all_patients()
        all_results = {}
        
        for patient in patients:
            results = await self.run_pipeline(patient.patient_id)
            all_results[patient.patient_id] = results
        
        return all_results

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for name, agent in self._agents.items():
            status[name] = {
                "registered": True,
                "type": type(agent).__name__,
            }
        
        for name in self._pipeline_order:
            if name not in status:
                status[name] = {
                    "registered": False,
                    "type": None,
                }
        
        return status
