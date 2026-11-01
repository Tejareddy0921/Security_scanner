import asyncio
from datetime import timedelta
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.errors import DuplicateResourceError
from app.core.security import InvalidTokenError, create_access_token, decode_access_token
from app.dependencies.auth import get_current_user
from app.services.auth_service import AuthService, InvalidCredentialsError


@pytest.fixture(autouse=True)
def use_inline_hash_worker_for_unit_tests(monkeypatch):
    async def run_inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr("app.services.auth_service.asyncio.to_thread", run_inline)


class MemoryUsers:
    def __init__(self):
        self.items = []

    async def find_by_email(self, email):
        return next((item for item in self.items if item["email"] == email), None)

    async def create(self, document):
        item = {"_id": ObjectId(), **document}
        self.items.append(item)
        return item


def test_registration_normalizes_email_hashes_password_and_returns_safe_user():
    users = MemoryUsers()
    response = asyncio.run(AuthService(users).register("  ALICE@example.com ", "Alice", "correct horse battery"))
    assert response.email == "alice@example.com"
    assert response.id
    assert not hasattr(response, "password_hash")
    assert users.items[0]["password_hash"] != "correct horse battery"
    assert users.items[0]["is_active"] is True


@pytest.mark.parametrize("field", ["full_name", "fullName", "name"])
def test_registration_accepts_common_name_field_spellings(field):
    request = {"email": "alice@example.com", field: "Alice", "password": "correct horse battery"}
    from app.schemas.auth import RegisterRequest

    assert RegisterRequest.model_validate(request).full_name == "Alice"


def test_registration_rejects_duplicate_normalized_email():
    service = AuthService(MemoryUsers())
    asyncio.run(service.register("alice@example.com", "Alice", "correct horse battery"))
    with pytest.raises(DuplicateResourceError):
        asyncio.run(service.register("ALICE@example.com", "Alice Two", "another safe password"))


def test_login_issues_jwt_and_rejects_bad_or_inactive_accounts():
    users = MemoryUsers()
    service = AuthService(users)
    asyncio.run(service.register("alice@example.com", "Alice", "correct horse battery"))
    result = asyncio.run(service.login("ALICE@example.com", "correct horse battery"))
    assert decode_access_token(result["access_token"])["sub"] == str(users.items[0]["_id"])
    assert result["user"].email == "alice@example.com"
    with pytest.raises(InvalidCredentialsError):
        asyncio.run(service.login("alice@example.com", "incorrect password"))
    users.items[0]["is_active"] = False
    with pytest.raises(InvalidCredentialsError):
        asyncio.run(service.login("alice@example.com", "correct horse battery"))


def test_invalid_and_expired_tokens_are_rejected():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not.a.jwt")
    expired = create_access_token("507f1f77bcf86cd799439011", timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired)


class MemoryCollection:
    def __init__(self, item=None):
        self.item = item
        self.indexes = []

    async def create_index(self, key, **kwargs):
        self.indexes.append((key, kwargs))

    async def find_one(self, query):
        if self.item is not None and all(self.item.get(key) == value for key, value in query.items()):
            return self.item
        return None


class MemoryDatabase:
    def __init__(self, user=None):
        self.collections = {
            name: MemoryCollection(user if name == "users" else None)
            for name in ("users", "scam_reports", "detection_results")
        }

    def __getitem__(self, name):
        return self.collections[name]


def request_for(database):
    state = SimpleNamespace(database=database, indexes_ready=False, indexes_lock=asyncio.Lock())
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_current_user_requires_active_account_and_initializes_indexes():
    user_id = ObjectId()
    user = {"_id": user_id, "is_active": True}
    database = MemoryDatabase(user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=create_access_token(str(user_id)))
    current = asyncio.run(get_current_user(request_for(database), credentials))
    assert current is user
    assert len(database["users"].indexes) == 1
    assert len(database["scam_reports"].indexes) == 2
    assert len(database["detection_results"].indexes) == 2


@pytest.mark.parametrize("token", [None, "bad-sub"])
def test_missing_or_malformed_credentials_return_401_without_database_access(token):
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    credentials = None if token is None else HTTPAuthorizationCredentials(scheme="Bearer", credentials=create_access_token(token))
    with pytest.raises(HTTPException) as error:
        asyncio.run(get_current_user(request, credentials))
    assert error.value.status_code == 401


def test_inactive_or_missing_user_cannot_authenticate():
    user_id = ObjectId()
    database = MemoryDatabase({"_id": user_id, "is_active": False})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=create_access_token(str(user_id)))
    with pytest.raises(HTTPException) as error:
        asyncio.run(get_current_user(request_for(database), credentials))
    assert error.value.status_code == 401

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=create_access_token(str(ObjectId())))
    with pytest.raises(HTTPException) as error:
        asyncio.run(get_current_user(request_for(MemoryDatabase()), credentials))
    assert error.value.status_code == 401
