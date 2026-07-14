from fastapi import APIRouter, Depends
from src.api.core.security import get_current_user

router = APIRouter()

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    A protected route. It requires a valid Supabase JWT in the Authorization header.
    FastAPI automatically handles extracting and verifying the token via the dependency.
    """
    return {
        "message": "You are authenticated!",
        # The 'sub' claim in a Supabase JWT is the user's UUID
        "user_id": current_user.get("sub"),
        "token_payload": current_user
    }
