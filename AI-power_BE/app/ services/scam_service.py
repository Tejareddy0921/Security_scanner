from app.repositories.scam_repository import ScamRepository
from app.schemas.scam import (
    ScamReportCreate,
)


class ScamService:

    def __init__(self):
        self.scam_repository = ScamRepository()

    async def create_report(
        self,
        user_id: str,
        report_data: ScamReportCreate
    ):
        """
        Create a scam report for the authenticated user.
        """

        if not report_data.content.strip():
            raise ValueError(
                "Scam report content cannot be empty"
            )

        report_document = {
            "user_id": user_id,
            "content": report_data.content.strip(),
            "source": report_data.source,
            "scam_type": None,
            "is_scam": None,
            "confidence_score": None,
            "explanation": None,
            "status": "pending",
        }

        created_report = (
            await self.scam_repository.create_report(
                report_document
            )
        )

        return self._serialize_report(created_report)

    async def get_user_reports(
        self,
        user_id: str
    ):
        """
        Get all scam reports belonging to the current user.
        """

        reports = (
            await self.scam_repository.get_by_user_id(
                user_id
            )
        )

        return [
            self._serialize_report(report)
            for report in reports
        ]

    async def get_report(
        self,
        report_id: str,
        user_id: str
    ):
        """
        Get one report, ensuring that it belongs
        to the authenticated user.
        """

        report = await self.scam_repository.get_by_id(
            report_id
        )

        if not report:
            raise ValueError("Scam report not found")

        # Important security check
        if str(report["user_id"]) != user_id:
            raise ValueError("Scam report not found")

        return self._serialize_report(report)

    async def update_report(
        self,
        report_id: str,
        user_id: str,
        update_data: dict
    ):
        """
        Update a scam report belonging to the user.
        """

        report = await self.scam_repository.get_by_id(
            report_id
        )

        if not report:
            raise ValueError("Scam report not found")

        if str(report["user_id"]) != user_id:
            raise ValueError("Scam report not found")

        updated_report = (
            await self.scam_repository.update_report(
                report_id,
                update_data
            )
        )

        if not updated_report:
            raise ValueError("Unable to update report")

        return self._serialize_report(updated_report)

    async def delete_report(
        self,
        report_id: str,
        user_id: str
    ):
        """
        Delete a scam report belonging to the user.
        """

        report = await self.scam_repository.get_by_id(
            report_id
        )

        if not report:
            raise ValueError("Scam report not found")

        if str(report["user_id"]) != user_id:
            raise ValueError("Scam report not found")

        deleted = await self.scam_repository.delete_report(
            report_id
        )

        if not deleted:
            raise ValueError("Unable to delete report")

        return True

    @staticmethod
    def _serialize_report(report: dict) -> dict:
        """
        Convert MongoDB document into API response.
        """

        return {
            "id": str(report["_id"]),
            "user_id": str(report["user_id"]),
            "content": report["content"],
            "source": report.get("source"),
            "scam_type": report.get("scam_type"),
            "is_scam": report.get("is_scam"),
            "confidence_score": report.get(
                "confidence_score"
            ),
            "explanation": report.get(
                "explanation"
            ),
            "status": report.get(
                "status",
                "pending"
            ),
            "created_at": report["created_at"],
        }