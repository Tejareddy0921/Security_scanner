from typing import Any

from bson import ObjectId


class ScamRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def find_owned(self, report_id: ObjectId, user_id: ObjectId) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": report_id, "user_id": user_id})

    async def contents_for_user(self, report_ids: list[ObjectId], user_id: ObjectId) -> dict[ObjectId, str]:
        if not report_ids:
            return {}
        cursor = self.collection.find(
            {"_id": {"$in": report_ids}, "user_id": user_id},
            {"_id": 1, "content": 1},
        )
        reports = await cursor.to_list(length=len(report_ids))
        return {report["_id"]: report["content"] for report in reports}

    async def list_for_user(self, user_id: ObjectId, limit: int = 100) -> list[dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def set_status(self, report_id: ObjectId, user_id: ObjectId, status: str, updated_at: Any) -> bool:
        result = await self.collection.update_one(
            {"_id": report_id, "user_id": user_id},
            {"$set": {"status": status, "updated_at": updated_at}},
        )
        return result.matched_count == 1
