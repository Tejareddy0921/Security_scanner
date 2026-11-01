from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_database


class DetectionRepository:
    """
    Handles MongoDB operations for detection results.
    """

    def __init__(self):
        self.db = get_database()
        self.collection = self.db["detection_results"]

    async def create_result(
        self,
        result_data: dict
    ):
        """
        Create a new detection result.
        """

        now = datetime.now(timezone.utc)

        result_data["created_at"] = (
            result_data.get("created_at", now)
        )

        result_data["updated_at"] = None

        result = await self.collection.insert_one(
            result_data
        )

        return await self.collection.find_one(
            {
                "_id": result.inserted_id
            }
        )

    async def get_by_id(
        self,
        detection_id: str
    ):
        """
        Get a detection result by MongoDB ObjectId.
        """

        if not ObjectId.is_valid(detection_id):
            return None

        return await self.collection.find_one(
            {
                "_id": ObjectId(detection_id)
            }
        )

    async def get_by_user_id(
        self,
        user_id: str
    ) -> list[dict]:
        """
        Get all detection results belonging
        to a specific user.
        """

        cursor = self.collection.find(
            {
                "user_id": user_id
            }
        ).sort(
            "created_at",
            -1
        )

        return await cursor.to_list(
            length=None
        )

    async def get_by_report_id(
        self,
        report_id: str
    ):
        """
        Get the detection result associated
        with a scam report.
        """

        return await self.collection.find_one(
            {
                "report_id": report_id
            }
        )

    async def update_result(
        self,
        detection_id: str,
        update_data: dict
    ):
        """
        Update an existing detection result.
        """

        if not ObjectId.is_valid(detection_id):
            return None

        update_data["updated_at"] = (
            datetime.now(timezone.utc)
        )

        return await self.collection.find_one_and_update(
            {
                "_id": ObjectId(detection_id)
            },
            {
                "$set": update_data
            },
            return_document=ReturnDocument.AFTER
        )

    async def delete_result(
        self,
        detection_id: str
    ) -> bool:
        """
        Delete a detection result.
        """

        if not ObjectId.is_valid(detection_id):
            return False

        result = await self.collection.delete_one(
            {
                "_id": ObjectId(detection_id)
            }
        )

        return result.deleted_count == 1