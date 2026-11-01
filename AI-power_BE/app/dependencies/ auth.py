from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository


security = HTTPBearer()

user_repository = UserRepository()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    """
    Get the currently authenticated user from the JWT.
    """

    token = credentials.credentials

    # ---------------------------------------------
    # 1. Decode and validate JWT
    # ---------------------------------------------

    try:
        payload = decode_access_token(token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ---------------------------------------------
    # 2. Get user ID from JWT
    # ---------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ---------------------------------------------
    # 3. Find user in MongoDB
    # ---------------------------------------------

    user = await user_repository.find_by_id(
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ---------------------------------------------
    # 4. Check account status
    # ---------------------------------------------

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user