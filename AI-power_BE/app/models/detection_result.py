from datetime import datetime
from enum import Enum
from typing import TypedDict

from bson import ObjectId


class ScamLabel(str, Enum):
    scam = "scam"
    not_scam = "not_scam"
    suspicious = "suspicious"


class DetectionResultDocument(TypedDict):
    _id: ObjectId
    user_id: ObjectId
    report_id: ObjectId
    label: str
    confidence_score: float
    scam_type: str | None
    risk_factors: list[str]
    recommendations: list[str]
    explanation: str
    model_name: str
    created_at: datetime
