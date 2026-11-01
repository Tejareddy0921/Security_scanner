import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from bson import ObjectId
from pydantic import ValidationError
from pymongo.errors import ServerSelectionTimeoutError

from app.core.database import get_database, lifespan
from app.core.errors import AIProviderError, AIProviderRateLimitError, AIServiceUnavailableError
from app.dependencies.auth import get_current_user
from app.main import app
from app.main import domain_error_handler, request_validation_error_handler
from app.dependencies.services import get_auth_service
from app.schemas.detection import DetectionRequest
from app.schemas.scam import ScamReportCreate
from app.schemas.user import UserResponse


def request(method, path, **kwargs):
    async def send():
        async with lifespan(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_startup_route_map_and_authentication_gate():
    expected = {
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("GET", "/users/me"),
        ("PUT", "/users/me"),
        ("DELETE", "/users/me"),
        ("POST", "/scams/report"),
        ("GET", "/scams/my-reports"),
        ("GET", "/scams/{report_id}"),
        ("POST", "/detection/analyze"),
        ("GET", "/detection/history"),
        ("GET", "/detection/{detection_id}"),
    }
    paths = app.openapi()["paths"]
    actual = {(method.upper(), path) for path, operations in paths.items() for method in operations}
    assert expected <= actual

    assert request("GET", "/").status_code == 200
    response = request("GET", "/users/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_request_validation_rejects_client_owned_ids_and_empty_detection_content():
    with pytest.raises(ValidationError):
        ScamReportCreate.model_validate({"content": "message", "user_id": "507f1f77bcf86cd799439011"})
    with pytest.raises(ValidationError):
        DetectionRequest.model_validate({"content": "   "})


def test_register_route_accepts_name_payload_and_returns_created_user():
    class StubAuthService:
        async def register(self, email, full_name, password):
            assert email == "alice@example.com"
            assert full_name == "Alice"
            assert password == "correct horse battery"
            return UserResponse(
                id="507f1f77bcf86cd799439011",
                email=email,
                full_name=full_name,
                is_active=True,
                created_at="2026-10-03T00:00:00+00:00",
                updated_at="2026-10-03T00:00:00+00:00",
            )

    async def provide_auth_service():
        return StubAuthService()

    app.dependency_overrides[get_auth_service] = provide_auth_service
    try:
        response = request(
            "POST",
            "/auth/register",
            json={"email": "alice@example.com", "name": "Alice", "password": "correct horse battery"},
        )
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert response.status_code == 201
    assert response.json()["full_name"] == "Alice"


def test_request_body_size_is_capped():
    response = request(
        "POST",
        "/auth/register",
        content=b"x" * 1_048_577,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413


def test_validation_error_response_does_not_echo_request_values():
    from fastapi.exceptions import RequestValidationError

    error = RequestValidationError(
        [{"loc": ("body", "email"), "msg": "Field required", "type": "missing", "input": {"password": "secret"}}]
    )
    request_scope = SimpleNamespace(method="POST", url=SimpleNamespace(path="/auth/register"))
    response = asyncio.run(request_validation_error_handler(request_scope, error))
    body = json.loads(response.body)
    assert body["detail"][0]["loc"] == ["body", "email"]
    assert "input" not in body["detail"][0]
    assert "secret" not in response.body.decode()


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (AIProviderRateLimitError("try later"), 429),
        (AIProviderError("provider rejected the request"), 502),
        (AIServiceUnavailableError("temporarily unavailable"), 503),
    ],
)
def test_provider_errors_have_distinct_safe_http_statuses(error, status_code):
    request_scope = SimpleNamespace(method="POST", url=SimpleNamespace(path="/detection/analyze"))
    response = asyncio.run(domain_error_handler(request_scope, error))
    assert response.status_code == status_code


class EmptyCursor:
    def sort(self, *args):
        return self

    def limit(self, *args):
        return self

    async def to_list(self, length):
        return []


class RecordingCollection:
    def __init__(self):
        self.queries = []

    def find(self, query, projection=None):
        self.queries.append(query)
        return EmptyCursor()


def test_detection_history_reads_mongodb_without_a_groq_client():
    user = {"_id": ObjectId(), "is_active": True}
    detections = RecordingCollection()
    database = {"detection_results": detections, "scam_reports": RecordingCollection()}

    async def provide_user():
        return user

    async def provide_database():
        return database

    app.dependency_overrides[get_current_user] = provide_user
    app.dependency_overrides[get_database] = provide_database
    try:
        response = request("GET", "/detection/history")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_database, None)

    assert response.status_code == 200
    assert response.json() == []
    assert detections.queries == [{"user_id": user["_id"]}]


def test_detection_history_returns_database_error_when_mongodb_query_fails():
    user = {"_id": ObjectId(), "is_active": True}

    class UnavailableCollection:
        def find(self, query, projection=None):
            raise ServerSelectionTimeoutError("database unavailable")

    database = {"detection_results": UnavailableCollection(), "scam_reports": UnavailableCollection()}

    async def provide_user():
        return user

    async def provide_database():
        return database

    app.dependency_overrides[get_current_user] = provide_user
    app.dependency_overrides[get_database] = provide_database
    try:
        response = request("GET", "/detection/history")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_database, None)

    assert response.status_code == 503
    assert response.json() == {"detail": "Database service is currently unavailable"}
