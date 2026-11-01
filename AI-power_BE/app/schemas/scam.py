from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings
from app.models.scam_report import ReportSource, ReportStatus


MAX_CONTENT_LENGTH = get_settings().max_content_length


class ScamReportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(min_length=1, max_length=MAX_CONTENT_LENGTH)
    source: ReportSource = ReportSource.other

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Content must not be blank")
        return value


class ScamReportResponse(BaseModel):
    id: str
    user_id: str
    content: str
    source: ReportSource
    status: ReportStatus
    created_at: str
    updated_at: str
