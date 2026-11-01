from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from app.core.errors import ResourceNotFoundError
from app.repositories.scam_repository import ScamRepository
from app.schemas.scam import ScamReportCreate, ScamReportResponse
from app.utils.helpers import isoformat, parse_object_id


def to_report_response(document: dict[str, Any]) -> ScamReportResponse:
    return ScamReportResponse(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        content=document["content"],
        source=document["source"],
        status=document["status"],
        created_at=isoformat(document["created_at"]),
        updated_at=isoformat(document["updated_at"]),
    )


class ScamService:
    def __init__(self, reports: ScamRepository) -> None:
        self.reports = reports

    async def create(self, user: dict[str, Any], request: ScamReportCreate) -> ScamReportResponse:
        now = datetime.now(UTC)
        document = await self.reports.create(
            {
                "user_id": user["_id"],
                "content": request.content,
                "source": request.source.value,
                "status": "submitted",
                "created_at": now,
                "updated_at": now,
            }
        )
        return to_report_response(document)

    async def list_mine(self, user: dict[str, Any]) -> list[ScamReportResponse]:
        documents = await self.reports.list_for_user(user["_id"])
        return [to_report_response(item) for item in documents]

    async def get_mine(self, user: dict[str, Any], report_id: str) -> ScamReportResponse:
        document = await self.reports.find_owned(parse_object_id(report_id), user["_id"])
        if document is None:
            raise ResourceNotFoundError("Scam report not found")
        return to_report_response(document)
