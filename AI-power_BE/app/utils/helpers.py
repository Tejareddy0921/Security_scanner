from datetime import UTC, datetime

from bson import ObjectId

from app.core.errors import InvalidInputError


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise InvalidInputError("Invalid resource ID")
    return ObjectId(value)


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
