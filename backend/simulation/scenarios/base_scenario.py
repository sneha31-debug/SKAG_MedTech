"""
Base scenario protocol for hospital simulations.
All scenarios should implement this interface.
"""
from typing import Protocol
from backend.simulation.hospital_sim import HospitalSimulator


class BaseScenario(Protocol):
    """Protocol for scenario implementations"""
    
    name: str
    description: str
    duration_minutes: float
    
    @staticmethod
    def setup(simulator: HospitalSimulator) -> None:
        """
        Configure the simulator with this scenario's patients and events.
        
        Args:
            simulator: HospitalSimulator instance to configure
        """
        ...
