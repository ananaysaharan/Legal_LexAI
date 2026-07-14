import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.api.config import settings

# This tells FastAPI to look for an Authorization header with a Bearer token
security = HTTPBearer()

def verify_token(token: str) -> dict:
    """
    Verifies the JWT token using the Supabase JWT secret.
    Returns the decoded payload if valid.
    """
    try:
        # Supabase uses HS256 for their JWTs
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False} # Often needed for Supabase depending on setup
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency that extracts the Bearer token, verifies it,
    and returns the user payload.
    Inject this into any endpoint that requires authentication.
    """
    token = credentials.credentials
    user_payload = verify_token(token)
    
    # We could also fetch the user from the database here using the user_payload['sub']
    # if we needed more than just the JWT claims.
    
    return user_payload
