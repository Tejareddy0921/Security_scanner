import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from bson import ObjectId
from groq import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from app.ai.groq_service import GroqService
from app.core.config import Settings
from app.core.errors import (
    AIProviderError,
    AIProviderRateLimitError,
    AIServiceUnavailableError,
    InvalidAIResponseError,
    ResourceNotFoundError,
)
from app.models.detection_result import ScamLabel
from app.schemas.detection import AIResult, DetectionRequest
from app.services.detection_service import DetectionService
from app.dependencies.services import get_detection_service


class MemoryReports:
    def __init__(self):
        self.items = []

    async def create(self, document):
        item = {"_id": ObjectId(), **document}
        self.items.append(item)
        return item

    async def set_status(self, report_id, user_id, status, updated_at):
        item = next((row for row in self.items if row["_id"] == report_id and row["user_id"] == user_id), None)
        if item is None:
            return False
        item.update(status=status, updated_at=updated_at)
        return True


class MemoryDetections:
    def __init__(self):
        self.items = []

    async def create(self, document):
        item = {"_id": ObjectId(), **document}
        self.items.append(item)
        return item

    async def list_for_user(self, user_id, limit=100):
        return [item for item in self.items if item["user_id"] == user_id][:limit]

    async def find_owned(self, detection_id, user_id):
        return next((item for item in self.items if item["_id"] == detection_id and item["user_id"] == user_id), None)


class Classifier:
    async def classify(self, content):
        return AIResult(
            label=ScamLabel.scam,
            confidence_score=0.96,
            scam_type="phishing",
            risk_factors=["Urgent request for credentials"],
            recommendations=["Do not open the link"],
            explanation="The message requests sensitive information through a link.",
        )


def test_analysis_saves_report_result_updates_status_and_supports_history():
    reports, detections = MemoryReports(), MemoryDetections()
    service = DetectionService(reports, detections, Classifier(), Settings(secret_key="a" * 40))
    user = {"_id": ObjectId()}
    response = asyncio.run(service.analyze(user, DetectionRequest(content="Verify your bank login now")))
    assert response.label == ScamLabel.scam
    assert response.confidence_score == 0.96
    assert response.model_name == "openai/gpt-oss-20b"
    assert reports.items[0]["status"] == "analyzed"
    assert detections.items[0]["user_id"] == user["_id"]
    assert detections.items[0]["report_id"] == reports.items[0]["_id"]
    assert len(asyncio.run(service.history(user))) == 1


def test_history_reads_saved_results_without_a_classifier():
    reports, detections = MemoryReports(), MemoryDetections()
    settings = Settings(secret_key="a" * 40)
    user = {"_id": ObjectId()}
    writer = DetectionService(reports, detections, Classifier(), settings)
    asyncio.run(writer.analyze(user, DetectionRequest(content="Verify your bank login now")))

    history_service = DetectionService(reports, detections, None, settings)
    history = asyncio.run(history_service.history(user))
    assert len(history) == 1
    assert history[0].label == ScamLabel.scam


def test_detection_service_dependency_does_not_require_groq_client_for_history():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    database = {"scam_reports": object(), "detection_results": object()}

    service = asyncio.run(get_detection_service(request, database))

    assert service.classifier is None


def test_analysis_without_a_groq_client_marks_report_failed():
    reports, detections = MemoryReports(), MemoryDetections()
    service = DetectionService(reports, detections, None, Settings(secret_key="a" * 40))

    with pytest.raises(AIServiceUnavailableError):
        asyncio.run(service.analyze({"_id": ObjectId()}, DetectionRequest(content="Suspicious message")))

    assert reports.items[0]["status"] == "failed"
    assert detections.items == []


@pytest.mark.parametrize("failure", [AIServiceUnavailableError("offline"), InvalidAIResponseError("invalid")])
def test_failed_analysis_marks_report_failed_and_does_not_save_detection(failure):
    class FailedClassifier:
        async def classify(self, content):
            raise failure

    reports, detections = MemoryReports(), MemoryDetections()
    service = DetectionService(reports, detections, FailedClassifier(), Settings(secret_key="a" * 40))
    with pytest.raises(type(failure)):
        asyncio.run(service.analyze({"_id": ObjectId()}, DetectionRequest(content="Suspicious message")))
    assert reports.items[0]["status"] == "failed"
    assert detections.items == []


def test_result_schema_rejects_invalid_label_confidence_and_empty_content():
    with pytest.raises(ValidationError):
        AIResult(label="probably_scam", confidence_score=0.8, explanation="x")
    with pytest.raises(ValidationError):
        AIResult(label="scam", confidence_score=1.5, explanation="x")
    with pytest.raises(ValidationError):
        AIResult(label="scam", confidence_score=True, explanation="x")
    with pytest.raises(ValidationError):
        DetectionRequest(content=" ")


def test_detection_lookup_is_scoped_to_owner():
    reports, detections = MemoryReports(), MemoryDetections()
    service = DetectionService(reports, detections, Classifier(), Settings(secret_key="a" * 40))
    user_a, user_b = {"_id": ObjectId()}, {"_id": ObjectId()}
    result = asyncio.run(service.analyze(user_a, DetectionRequest(content="Message")))
    with pytest.raises(ResourceNotFoundError):
        asyncio.run(service.get_mine(user_b, result.detection_id))


def _groq_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )


def _groq_client(content=None, error=None):
    create = AsyncMock(return_value=_groq_response(content))
    if error is not None:
        create.side_effect = error
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
    )


def test_groq_service_uses_strict_schema_and_validates_structured_response():
    content = json.dumps({
        "label": "scam",
        "confidence_score": 0.72,
        "scam_type": "phishing",
        "risk_factors": ["Requests a one-time code"],
        "recommendations": ["Do not share the code"],
        "explanation": "The message asks for sensitive authentication information.",
    })
    client = _groq_client(content)

    async def run():
        result = await GroqService(client, Settings(secret_key="a" * 40)).classify([])
        return result

    result = asyncio.run(run())
    request = client.chat.completions.create.call_args.kwargs
    assert result.label == ScamLabel.scam
    assert result.scam_type == "phishing"
    assert request["model"] == "openai/gpt-oss-20b"
    assert request["response_format"]["json_schema"]["strict"] is True
    assert set(request["response_format"]["json_schema"]["schema"]["required"]) == {
        "label", "confidence_score", "scam_type", "risk_factors", "recommendations", "explanation"
    }


def test_groq_service_accepts_a_normal_low_risk_message_result():
    content = json.dumps({
        "label": "not_scam",
        "confidence_score": 0.88,
        "scam_type": None,
        "risk_factors": [],
        "recommendations": ["Continue using your usual verification habits."],
        "explanation": (
            "The message contains routine appointment information and no request for money or sensitive details."
        ),
    })

    async def run():
        return await GroqService(_groq_client(content), Settings(secret_key="a" * 40)).classify([])

    assert asyncio.run(run()).label == ScamLabel.not_scam


@pytest.mark.parametrize("content", ["not json", '{"label":"scam","confidence_score":2,"explanation":"bad"}', "{}"])
def test_groq_service_rejects_malformed_or_out_of_range_results(content):
    async def run():
        client = _groq_client(content)
        await GroqService(client, Settings(secret_key="a" * 40)).classify([])

    with pytest.raises(InvalidAIResponseError):
        asyncio.run(run())


@pytest.mark.parametrize(
    ("error_type", "expected_error"),
    [
        ("connection", AIServiceUnavailableError),
        ("timeout", AIServiceUnavailableError),
        ("rate_limit", AIProviderRateLimitError),
        ("authentication", AIProviderError),
    ],
)
def test_groq_service_maps_provider_failures_to_safe_errors(error_type, expected_error):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    status_code = 401 if error_type == "authentication" else 429
    response = httpx.Response(status_code, request=request)
    errors = {
        "connection": APIConnectionError(message="connection refused", request=request),
        "timeout": APITimeoutError(request=request),
        "rate_limit": RateLimitError(message="provider rate limit", response=response, body={}),
        "authentication": AuthenticationError(message="invalid API key", response=response, body={}),
    }
    error = errors[error_type]

    async def run():
        client = _groq_client(error=error)
        await GroqService(client, Settings(secret_key="a" * 40)).classify([])

    with pytest.raises(expected_error) as raised:
        asyncio.run(run())
    assert "invalid API key" not in str(raised.value)
    assert "provider rate limit" not in str(raised.value)
