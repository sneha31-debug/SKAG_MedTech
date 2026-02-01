"""
Agent status routes for AdaptiveCare API

Provides endpoints for monitoring AI agent status.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime

router = APIRouter()


# Default agent configurations  
DEFAULT_AGENTS = [
    {
        "agent_name": "RiskMonitor",
        "display_name": "Risk Monitor",
        "description": "Monitors patient risk levels and detects deterioration patterns",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "CapacityIntelligence", 
        "display_name": "Capacity Intelligence",
        "description": "Tracks bed availability and staff workload across units",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "FlowOrchestrator",
        "display_name": "Flow Orchestrator", 
        "description": "Optimizes patient flow and bed assignments",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    },
    {
        "agent_name": "EscalationDecision",
        "display_name": "Escalation Decision",
        "description": "Makes AI-powered decisions for patient escalation",
        "is_active": True,
        "is_registered": True,
        "decision_count": 0,
        "last_decision_time": None
    }
]


@router.get("/status")
async def get_agents_status() -> List[Dict[str, Any]]:
    """Get status of all AI agents."""
    from backend.core.state_manager import get_state_manager
    
    state_manager = get_state_manager()
    all_decisions = state_manager.get_decisions()
    
    # Count decisions per agent
    agent_decision_counts = {}
    agent_last_decision_times = {}
    
    for decision in all_decisions:
        agent_name = getattr(decision, 'agent_name', 'Unknown')
        agent_decision_counts[agent_name] = agent_decision_counts.get(agent_name, 0) + 1
        
        # Track last decision time
        if agent_name not in agent_last_decision_times or decision.timestamp > agent_last_decision_times[agent_name]:
            agent_last_decision_times[agent_name] = decision.timestamp
    
    # Update agent status with actual counts
    agents_with_counts = []
    for agent in DEFAULT_AGENTS:
        agent_copy = agent.copy()
        agent_name = agent["agent_name"]
        agent_copy["decision_count"] = agent_decision_counts.get(agent_name, 0)
        agent_copy["last_decision_time"] = agent_last_decision_times.get(agent_name)
        agents_with_counts.append(agent_copy)
    
    return agents_with_counts


@router.get("/list")
async def list_agents():
    """List all registered agents."""
    return {
        "agents": [a["agent_name"] for a in DEFAULT_AGENTS],
        "count": len(DEFAULT_AGENTS)
    }


@router.get("/{agent_name}/status")
async def get_agent_status(agent_name: str) -> Dict[str, Any]:
    """Get status of a specific agent."""
    for agent in DEFAULT_AGENTS:
        if agent["agent_name"] == agent_name:
            return agent
    return {"error": f"Agent {agent_name} not found"}
