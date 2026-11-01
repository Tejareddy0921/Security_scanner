import asyncio
from datetime import UTC, datetime
from typing import Any

from app.core.errors import AuthenticationError, DuplicateResourceError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.utils.mappers import to_user_response


class InvalidCredentialsError(AuthenticationError):
    pass


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, email: str, full_name: str, password: str) -> UserResponse:
        normalized_email = email.strip().lower()
        if await self.users.find_by_email(normalized_email):
            raise DuplicateResourceError("An account with this email already exists")
        now = datetime.now(UTC)
        password_hash = await asyncio.to_thread(hash_password, password)
        user = await self.users.create(
            {
                "email": normalized_email,
                "full_name": full_name.strip(),
                "password_hash": password_hash,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )
        return to_user_response(user)

    async def login(self, email: str, password: str) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        user = await self.users.find_by_email(normalized_email)
        if user is None:
            # Keep the verification cost similar for unknown email addresses.
            await asyncio.to_thread(hash_password, password)
            raise InvalidCredentialsError("Invalid email or password")
        valid = await asyncio.to_thread(verify_password, password, user["password_hash"])
        if not valid or not user.get("is_active", False):
            raise InvalidCredentialsError("Invalid email or password")
        return {"access_token": create_access_token(str(user["_id"])), "user": to_user_response(user)}
