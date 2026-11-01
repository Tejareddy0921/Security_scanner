import logging
from datetime import UTC, datetime
from typing import Any

from app.ai.classifier import ScamClassifier
from app.core.config import Settings
from app.core.errors import AIAnalysisError, AIServiceUnavailableError, ResourceNotFoundError
from app.repositories.detection_repository import DetectionRepository
from app.repositories.scam_repository import ScamRepository
from app.schemas.detection import AIResult, DetectionRequest, DetectionResponse
from app.utils.helpers import isoformat, parse_object_id


logger = logging.getLogger("app.detection")


def to_detection_response(document: dict[str, Any], content: str) -> DetectionResponse:
    return DetectionResponse(
        detection_id=str(document["_id"]),
        report_id=str(document["report_id"]),
        content=content,
        model_name=document["model_name"],
        created_at=isoformat(document["created_at"]),
        label=document["label"],
        confidence_score=document["confidence_score"],
        scam_type=document.get("scam_type"),
        risk_factors=document.get("risk_factors", []),
        recommendations=document.get("recommendations", []),
        explanation=document["explanation"],
    )


class DetectionService:
    def __init__(
        self,
        reports: ScamRepository,
        detections: DetectionRepository,
        classifier: ScamClassifier | None,
        settings: Settings,
    ) -> None:
        self.reports = reports
        self.detections = detections
        self.classifier = classifier
        self.settings = settings

    async def analyze(self, user: dict[str, Any], request: DetectionRequest) -> DetectionResponse:
        now = datetime.now(UTC)
        report = await self.reports.create(
            {
                "user_id": user["_id"],
                "content": request.content,
                "source": request.source.value,
                "status": "submitted",
                "created_at": now,
                "updated_at": now,
            }
        )
        try:
            if self.classifier is None:
                logger.error("detection_failed model=%s error_type=groq_api_key_missing", self.settings.groq_model)
                raise AIServiceUnavailableError("The analysis service is not configured")
            ai_result: AIResult = await self.classifier.classify(request.content)
        except AIAnalysisError as exc:
            await self.reports.set_status(report["_id"], user["_id"], "failed", datetime.now(UTC))
            logger.error("detection_failed model=%s error_type=%s", self.settings.groq_model, type(exc).__name__)
            raise

        detected_at = datetime.now(UTC)
        detection = await self.detections.create(
            {
                "user_id": user["_id"],
                "report_id": report["_id"],
                **ai_result.model_dump(mode="json"),
                "model_name": self.settings.groq_model,
                "created_at": detected_at,
            }
        )
        updated = await self.reports.set_status(report["_id"], user["_id"], "analyzed", detected_at)
        if not updated:
            raise ResourceNotFoundError("Scam report not found")
        logger.info(
            "detection_completed model=%s label=%s report_id=%s",
            self.settings.groq_model,
            ai_result.label.value,
            report["_id"],
        )
        return to_detection_response(detection, request.content)

    async def history(self, user: dict[str, Any]) -> list[DetectionResponse]:
        items = await self.detections.list_for_user(user["_id"])
        contents = (
            await self.reports.contents_for_user(
                [item["report_id"] for item in items],
                user["_id"],
            )
            if hasattr(self.reports, "contents_for_user")
            else {}
        )
        return [to_detection_response(item, contents.get(item["report_id"], "")) for item in items]

    async def get_mine(self, user: dict[str, Any], detection_id: str) -> DetectionResponse:
        document = await self.detections.find_owned(parse_object_id(detection_id), user["_id"])
        if document is None:
            raise ResourceNotFoundError("Detection result not found")
        report = await self.reports.find_owned(document["report_id"], user["_id"])
        if report is None:
            raise ResourceNotFoundError("Detection report not found")
        return to_detection_response(document, report["content"])
