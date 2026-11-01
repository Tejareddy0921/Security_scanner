from typing import Any

from app.schemas.user import UserResponse
from app.utils.helpers import isoformat


def to_user_response(document: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=str(document["_id"]),
        email=document["email"],
        full_name=document["full_name"],
        is_active=document["is_active"],
        created_at=isoformat(document["created_at"]),
        updated_at=isoformat(document["updated_at"]),
    )
