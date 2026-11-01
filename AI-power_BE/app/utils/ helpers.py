from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """
    Return the current UTC datetime.
    """
    return datetime.now(timezone.utc)


def clean_text(value: str) -> str:
    """
    Remove unnecessary whitespace from text.
    """

    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    return " ".join(value.strip().split())


def normalize_email(email: str) -> str:
    """
    Normalize an email address.
    """

    if not isinstance(email, str):
        raise ValueError("Email must be a string")

    return email.strip().lower()


def is_empty(value: Any) -> bool:
    """
    Check whether a value is None or an empty string.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def serialize_object_id(document: dict) -> dict:
    """
    Convert MongoDB ObjectId to string.

    Useful when preparing MongoDB documents
    for API responses.
    """

    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]

    return document 