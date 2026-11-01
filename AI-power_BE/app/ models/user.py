from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """
    User document stored in MongoDB.
    """

    id: Optional[str] = Field(
        default=None,
        description="MongoDB document ID"
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password_hash: str = Field(
        ...,
        description="Hashed password"
    )

    role: UserRole = Field(
        default=UserRole.USER
    )

    is_active: bool = Field(
        default=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: Optional[datetime] = None