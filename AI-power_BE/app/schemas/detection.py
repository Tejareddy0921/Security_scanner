import math

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings
from app.models.detection_result import ScamLabel
from app.models.scam_report import ReportSource


class DetectionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(min_length=1, max_length=get_settings().max_content_length)
    source: ReportSource = ReportSource.other

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Content must not be blank")
        return value


class AIResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    label: ScamLabel
    confidence_score: float = Field(ge=0, le=1)
    scam_type: str | None = Field(default=None, max_length=100)
    risk_factors: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)
    explanation: str = Field(min_length=1, max_length=2_000)

    @field_validator("confidence_score", mode="before")
    @classmethod
    def confidence_must_be_numeric(cls, value):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (isinstance(value, float) and not math.isfinite(value))
        ):
            raise ValueError("confidence_score must be a number")
        return value

    @field_validator("scam_type")
    @classmethod
    def validate_scam_type(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("scam_type must be non-empty when provided")
        return value

    @field_validator("risk_factors", "recommendations")
    @classmethod
    def validate_text_lists(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 300 for value in values):
            raise ValueError("AI result contains an invalid list item")
        return values


class DetectionResponse(AIResult):
    detection_id: str
    report_id: str
    content: str
    model_name: str
    created_at: str
