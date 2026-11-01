from datetime import datetime
from typing import TypedDict

from bson import ObjectId


class UserDocument(TypedDict):
    _id: ObjectId
    email: str
    full_name: str
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
