from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import ai, health, users, cases, intents, memory, plans, workers, orchestration
from src.api.config import settings

def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title="AI SaaS Backend",
        description="FastAPI Backend for AI SaaS Platform",
        version="0.1.0",
    )

    # Configure CORS for local development (will be tightened for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(cases.router, prefix="/cases", tags=["cases"])
    app.include_router(intents.router, prefix="/intents", tags=["intents"])
    app.include_router(plans.router, prefix="/plans", tags=["plans"])
    app.include_router(workers.router, prefix="/workers", tags=["workers"])
    app.include_router(orchestration.router, prefix="/orchestration", tags=["orchestration"])
    app.include_router(ai.router, prefix="/ai", tags=["ai"])
    app.include_router(memory.router, prefix="/memory", tags=["memory"])

    return app

# The main application instance used by Uvicorn
app = create_app()
