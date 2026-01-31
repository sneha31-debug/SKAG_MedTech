from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.models.decision import Decision


class BaseAgent(ABC):
    
    def __init__(self, event_bus, state_manager):
        self.event_bus = event_bus
        self.state = state_manager
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def decide(self, observations: Dict[str, Any]) -> Decision:
        pass

    async def execute(self, context: Dict[str, Any]) -> Decision:
        observations = await self.observe(context)
        decision = await self.decide(observations)
        await self.event_bus.publish(f"{self.name}.decision", decision)
        return decision
