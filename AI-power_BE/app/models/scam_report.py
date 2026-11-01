from datetime import datetime
from enum import Enum
from typing import TypedDict

from bson import ObjectId


class ReportSource(str, Enum):
    email = "email"
    sms = "sms"
    phone = "phone"
    website = "website"
    social_media = "social_media"
    other = "other"


class ReportStatus(str, Enum):
    submitted = "submitted"
    analyzed = "analyzed"
    failed = "failed"


class ScamReportDocument(TypedDict):
    _id: ObjectId
    user_id: ObjectId
    content: str
    source: str
    status: str
    created_at: datetime
    updated_at: datetime
