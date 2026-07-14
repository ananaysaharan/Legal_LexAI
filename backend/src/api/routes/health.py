from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    message: str

@router.get("/", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """
    Simple health check endpoint.
    Used by orchestrators (like Docker/Kubernetes) or load balancers 
    to verify the application is up and running.
    """
    return HealthResponse(
        status="healthy",
        message="API is running"
    )
