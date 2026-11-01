import asyncio
from datetime import UTC, datetime

import pytest
from bson import ObjectId
from pydantic import ValidationError

from app.core.errors import DuplicateResourceError, ResourceNotFoundError
from app.schemas.user import UserUpdateRequest
from app.services.user_service import UserService


class MemoryUsers:
    def __init__(self, users):
        self.users = users

    async def find_by_email(self, email):
        return next((user for user in self.users if user["email"] == email), None)

    async def update(self, user_id, values):
        user = next((user for user in self.users if user["_id"] == user_id), None)
        if user is not None:
            user.update(values)
        return user

    async def deactivate(self, user_id, updated_at):
        user = next((user for user in self.users if user["_id"] == user_id), None)
        if user is None or not user["is_active"]:
            return False
        user.update(is_active=False, updated_at=updated_at)
        return True


def make_user(email="alice@example.com"):
    now = datetime.now(UTC)
    return {
        "_id": ObjectId(),
        "email": email,
        "full_name": "Alice",
        "password_hash": "private-hash",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def test_profile_response_is_safe_and_update_changes_only_allowed_fields():
    user = make_user()
    service = UserService(MemoryUsers([user]))
    profile = asyncio.run(service.get_me(user))
    assert profile.email == "alice@example.com"
    assert not hasattr(profile, "password_hash")

    updated = asyncio.run(service.update_me(user, UserUpdateRequest(full_name="Alice Updated")))
    assert updated.full_name == "Alice Updated"
    assert updated.updated_at >= profile.updated_at


def test_profile_email_update_normalizes_and_rejects_duplicates():
    user, other = make_user(), make_user("other@example.com")
    service = UserService(MemoryUsers([user, other]))
    updated = asyncio.run(service.update_me(user, UserUpdateRequest(email="  alice.new@example.com  ")))
    assert updated.email == "alice.new@example.com"

    with pytest.raises(DuplicateResourceError):
        asyncio.run(service.update_me(user, UserUpdateRequest(email="other@example.com")))


def test_profile_delete_deactivates_account_and_preserves_document():
    user = make_user()
    users = MemoryUsers([user])
    service = UserService(users)
    asyncio.run(service.deactivate(user))
    assert user["is_active"] is False
    assert len(users.users) == 1

    with pytest.raises(ResourceNotFoundError):
        asyncio.run(service.deactivate(user))


@pytest.mark.parametrize("payload", [{}, {"full_name": None}, {"password": "new password"}])
def test_profile_update_rejects_empty_or_unsupported_fields(payload):
    with pytest.raises(ValidationError):
        UserUpdateRequest.model_validate(payload)
