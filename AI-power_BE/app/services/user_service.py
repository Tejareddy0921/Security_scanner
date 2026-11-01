from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from app.core.errors import DuplicateResourceError, ResourceNotFoundError
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdateRequest
from app.utils.mappers import to_user_response


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def get_me(self, user: dict[str, Any]) -> UserResponse:
        if not user.get("is_active", False):
            raise ResourceNotFoundError("User not found")
        return to_user_response(user)

    async def update_me(self, user: dict[str, Any], request: UserUpdateRequest) -> UserResponse:
        updates: dict[str, Any] = {}
        if "email" in request.model_fields_set and request.email:
            email = str(request.email).strip().lower()
            existing = await self.users.find_by_email(email)
            if existing is not None and existing["_id"] != user["_id"]:
                raise DuplicateResourceError("An account with this email already exists")
            updates["email"] = email
        if "full_name" in request.model_fields_set and request.full_name is not None:
            updates["full_name"] = request.full_name.strip()
        updates["updated_at"] = datetime.now(UTC)
        updated = await self.users.update(user["_id"], updates)
        if updated is None:
            raise ResourceNotFoundError("User not found")
        return to_user_response(updated)

    async def deactivate(self, user: dict[str, Any]) -> None:
        changed = await self.users.deactivate(user["_id"], datetime.now(UTC))
        if not changed:
            raise ResourceNotFoundError("User not found")
