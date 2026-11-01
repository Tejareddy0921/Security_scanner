from typing import Any

from bson import ObjectId


class DetectionRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def find_owned(self, detection_id: ObjectId, user_id: ObjectId) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": detection_id, "user_id": user_id})

    async def list_for_user(self, user_id: ObjectId, limit: int = 100) -> list[dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
