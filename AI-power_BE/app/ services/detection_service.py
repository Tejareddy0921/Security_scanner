import time
from datetime import datetime, timezone

from app.ai.classifier import ScamClassifier
from app.repositories.detection_repository import DetectionRepository
from app.repositories.scam_repository import ScamRepository


class DetectionService:

    def __init__(self):
        self.detection_repository = DetectionRepository()
        self.scam_repository = ScamRepository()
        self.classifier = ScamClassifier()

    async def analyze(
        self,
        user_id: str,
        content: str,
        source: str | None = None
    ):
        """
        Analyze submitted content and store the detection result.
        """

        if not content or not content.strip():
            raise ValueError(
                "Content cannot be empty"
            )

        content = content.strip()

        start_time = time.perf_counter()

        # -------------------------------------------------
        # 1. Create the original scam report
        # -------------------------------------------------

        report_document = {
            "user_id": user_id,
            "content": content,
            "source": source,
            "scam_type": None,
            "is_scam": None,
            "confidence_score": None,
            "explanation": None,
            "status": "processing",
            "created_at": datetime.now(timezone.utc),
        }

        report = await self.scam_repository.create_report(
            report_document
        )

        report_id = str(report["_id"])

        try:

            # -------------------------------------------------
            # 2. Run AI detection
            # -------------------------------------------------

            ai_result = await self.classifier.predict(
                content
            )

            # Example expected result:
            #
            # {
            #     "label": "scam",
            #     "confidence_score": 0.96,
            #     "scam_type": "phishing",
            #     "explanation": "...",
            #     "risk_factors": [...],
            #     "recommendations": [...]
            # }

            processing_time = (
                time.perf_counter() - start_time
            ) * 1000

            # -------------------------------------------------
            # 3. Save detection result
            # -------------------------------------------------

            detection_document = {
                "report_id": report_id,
                "user_id": user_id,
                "status": "completed",
                "label": ai_result.get("label"),
                "confidence_score": ai_result.get(
                    "confidence_score"
                ),
                "scam_type": ai_result.get(
                    "scam_type"
                ),
                "explanation": ai_result.get(
                    "explanation"
                ),
                "risk_factors": ai_result.get(
                    "risk_factors",
                    []
                ),
                "recommendations": ai_result.get(
                    "recommendations",
                    []
                ),
                "model_name": ai_result.get(
                    "model_name"
                ),
                "processing_time_ms": processing_time,
                "created_at": datetime.now(
                    timezone.utc
                ),
            }

            detection = (
                await self.detection_repository.create_result(
                    detection_document
                )
            )

            # -------------------------------------------------
            # 4. Update original report
            # -------------------------------------------------

            await self.scam_repository.update_report(
                report_id,
                {
                    "scam_type": ai_result.get(
                        "scam_type"
                    ),
                    "is_scam": (
                        ai_result.get("label") == "scam"
                    ),
                    "confidence_score": ai_result.get(
                        "confidence_score"
                    ),
                    "explanation": ai_result.get(
                        "explanation"
                    ),
                    "status": "completed",
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

            return self._serialize_result(
                detection
            )

        except Exception as exc:

            # -------------------------------------------------
            # 5. Mark report as failed
            # -------------------------------------------------

            await self.scam_repository.update_report(
                report_id,
                {
                    "status": "failed",
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

            raise RuntimeError(
                f"Scam detection failed: {str(exc)}"
            )

    async def get_user_history(
        self,
        user_id: str
    ):
        """
        Get detection history for the authenticated user.
        """

        results = (
            await self.detection_repository.get_by_user_id(
                user_id
            )
        )

        return [
            self._serialize_result(result)
            for result in results
        ]

    async def get_result(
        self,
        detection_id: str,
        user_id: str
    ):
        """
        Get one detection result belonging to the user.
        """

        result = (
            await self.detection_repository.get_by_id(
                detection_id
            )
        )

        if not result:
            return None

        # Security: user can only access own result
        if str(result["user_id"]) != user_id:
            return None

        return self._serialize_result(result)

    @staticmethod
    def _serialize_result(
        result: dict
    ) -> dict:
        """
        Convert MongoDB document into API response.
        """

        return {
            "id": str(result["_id"]),
            "report_id": str(result["report_id"]),
            "user_id": str(result["user_id"]),
            "status": result.get(
                "status",
                "pending"
            ),
            "label": result.get("label"),
            "confidence_score": result.get(
                "confidence_score"
            ),
            "scam_type": result.get(
                "scam_type"
            ),
            "explanation": result.get(
                "explanation"
            ),
            "risk_factors": result.get(
                "risk_factors",
                []
            ),
            "recommendations": result.get(
                "recommendations",
                []
            ),
            "model_name": result.get(
                "model_name"
            ),
            "processing_time_ms": result.get(
                "processing_time_ms"
            ),
            "created_at": result.get(
                "created_at"
            ),
            "updated_at": result.get(
                "updated_at"
            ),
        }