from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core import settings, event_bus, state_manager, Orchestrator
from backend.api.routes import patients, decisions, simulation, agents
from backend.api.websocket import router as ws_router


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Multi-Agent Hospital Patient Flow Intelligence System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator(event_bus, state_manager)

app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "simulation_running": state_manager.is_simulation_running(),
        "agents_registered": orchestrator.list_agents(),
    }
