import asyncio

import pytest
from bson import ObjectId
from pydantic import ValidationError

from app.core.errors import ResourceNotFoundError
from app.models.scam_report import ReportSource
from app.schemas.scam import ScamReportCreate
from app.services.scam_service import ScamService


class MemoryReports:
    def __init__(self):
        self.items = []

    async def create(self, document):
        item = {"_id": ObjectId(), **document}
        self.items.append(item)
        return item

    async def find_owned(self, report_id, user_id):
        return next((item for item in self.items if item["_id"] == report_id and item["user_id"] == user_id), None)

    async def list_for_user(self, user_id, limit=100):
        return [item for item in self.items if item["user_id"] == user_id][:limit]


def test_report_creation_uses_authenticated_user_and_lists_only_owned_reports():
    reports = MemoryReports()
    service = ScamService(reports)
    user_a, user_b = {"_id": ObjectId()}, {"_id": ObjectId()}
    created = asyncio.run(service.create(user_a, ScamReportCreate(content="A suspicious payment request", source=ReportSource.sms)))
    asyncio.run(service.create(user_b, ScamReportCreate(content="Other user's message")))
    assert created.user_id == str(user_a["_id"])
    assert len(asyncio.run(service.list_mine(user_a))) == 1
    assert created.status == "submitted"


def test_report_lookup_is_scoped_to_owner():
    reports = MemoryReports()
    service = ScamService(reports)
    user_a, user_b = {"_id": ObjectId()}, {"_id": ObjectId()}
    created = asyncio.run(service.create(user_a, ScamReportCreate(content="Suspicious link")))
    with pytest.raises(ResourceNotFoundError):
        asyncio.run(service.get_mine(user_b, created.id))


@pytest.mark.parametrize(
    "payload",
    [
        {"content": "   "},
        {"content": "Suspicious", "user_id": str(ObjectId())},
        {"content": "Suspicious", "source": "unrecognized"},
    ],
)
def test_report_validation_rejects_blank_content_client_user_id_and_invalid_source(payload):
    with pytest.raises(ValidationError):
        ScamReportCreate.model_validate(payload)


def test_report_content_limit_is_enforced():
    with pytest.raises(ValidationError):
        ScamReportCreate(content="x" * 20_001)
