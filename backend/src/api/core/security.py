import jwt
from jwt import PyJWKClient
import base64
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.api.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Supabase JWKS endpoint for asymmetric tokens (e.g. ES256)
jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
jwks_client = PyJWKClient(jwks_url)

def verify_token(token: str) -> dict:
    """
    Verifies the JWT token using Supabase JWKS (for ES256/asymmetric tokens)
    or the Supabase JWT secret (for HS256 symmetric tokens).
    Returns the decoded payload if valid.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg.startswith("ES") or alg.startswith("RS"):
            # Asymmetric algorithm (ES256 / RS256) used by newer Supabase projects
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                options={"verify_aud": False}
            )
            return payload
        else:
            # Symmetric algorithm (HS256)
            secret_candidates = []
            try:
                secret_candidates.append(base64.b64decode(settings.supabase_jwt_secret))
            except Exception:
                pass
            if isinstance(settings.supabase_jwt_secret, str):
                secret_candidates.append(settings.supabase_jwt_secret.encode('utf-8'))
            secret_candidates.append(settings.supabase_jwt_secret)

            last_error = None
            for secret in secret_candidates:
                try:
                    payload = jwt.decode(
                        token,
                        secret,
                        algorithms=["HS256"],
                        options={"verify_aud": False}
                    )
                    return payload
                except jwt.InvalidTokenError as e:
                    last_error = e
            raise last_error or jwt.InvalidTokenError("Could not verify HS256 signature")

    except jwt.ExpiredSignatureError as e:
        logger.error(f"JWT expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT invalid: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency that extracts the Bearer token, verifies it,
    and returns the user payload.
    """
    token = credentials.credentials
    return verify_token(token)
