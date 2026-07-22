from fastapi import APIRouter, Depends

from src.api.core.security import get_current_user
from src.api.schemas.intent import Intent, IntentDetectionRequest
from src.api.services.intent_detection import RuleBasedIntentDetector


router = APIRouter()
detector = RuleBasedIntentDetector()


@router.post("/detect", response_model=Intent)
async def detect_intent(
    request: IntentDetectionRequest,
    _current_user: dict = Depends(get_current_user),
) -> Intent:
    """Classify a request only; downstream planning is intentionally not invoked."""
    return detector.detect(request.request)
