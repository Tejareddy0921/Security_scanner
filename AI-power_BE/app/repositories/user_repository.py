from typing import Any

from bson import ObjectId


class UserRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"email": email})

    async def find_by_id(self, user_id: ObjectId) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": user_id})

    async def update(self, user_id: ObjectId, values: dict[str, Any]) -> dict[str, Any] | None:
        await self.collection.update_one({"_id": user_id}, {"$set": values})
        return await self.find_by_id(user_id)

    async def deactivate(self, user_id: ObjectId, updated_at: Any) -> bool:
        result = await self.collection.update_one(
            {"_id": user_id, "is_active": True},
            {"$set": {"is_active": False, "updated_at": updated_at}},
        )
        return result.modified_count == 1
