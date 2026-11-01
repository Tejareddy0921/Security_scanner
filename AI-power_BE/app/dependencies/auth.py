import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import ensure_indexes, get_database
from app.core.errors import InvalidInputError
from app.core.security import InvalidTokenError, decode_access_token
from app.repositories.user_repository import UserRepository
from app.utils.helpers import parse_object_id


_bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("app.auth")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    missing_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Bearer access token required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        logger.info("authentication_failed reason=missing_bearer_token")
        raise missing_credentials
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = parse_object_id(claims["sub"])
    except (InvalidTokenError, InvalidInputError, KeyError, ValueError):
        logger.info("authentication_failed reason=invalid_or_expired_token")
        raise unauthorized from None
    database = await get_database(request)
    await ensure_indexes(request, database)
    user = await UserRepository(database["users"]).find_by_id(user_id)
    if user is None or not user.get("is_active", False):
        logger.info("authentication_failed reason=inactive_or_missing_user")
        raise unauthorized
    return user
