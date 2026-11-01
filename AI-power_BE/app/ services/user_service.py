from datetime import datetime, timezone

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:

    def __init__(self):
        self.user_repository = UserRepository()

    async def get_user_by_id(self, user_id: str):
        """
        Get a user by MongoDB ID.
        """

        user = await self.user_repository.find_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        return self._serialize_user(user)

    async def update_user(
        self,
        user_id: str,
        user_data: UserUpdate
    ):
        """
        Update the authenticated user's profile.
        """

        # Only include fields actually supplied by the user
        update_data = user_data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        if not update_data:
            raise ValueError(
                "No data provided for update"
            )

        # Check whether the new email belongs to another user
        if "email" in update_data:

            existing_user = (
                await self.user_repository.find_by_email(
                    update_data["email"]
                )
            )

            if existing_user and str(
                existing_user["_id"]
            ) != user_id:
                raise ValueError(
                    "Email is already in use"
                )

        update_data["updated_at"] = (
            datetime.now(timezone.utc)
        )

        updated_user = (
            await self.user_repository.update_user(
                user_id,
                update_data
            )
        )

        if not updated_user:
            raise ValueError("User not found")

        return self._serialize_user(updated_user)

    async def delete_user(self, user_id: str):
        """
        Delete the authenticated user's account.
        """

        deleted = await self.user_repository.delete_user(
            user_id
        )

        if not deleted:
            raise ValueError("User not found")

        return True

    @staticmethod
    def _serialize_user(user: dict) -> dict:
        """
        Convert MongoDB user document into
        a safe API response.

        Never expose password_hash.
        """

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"],
        }