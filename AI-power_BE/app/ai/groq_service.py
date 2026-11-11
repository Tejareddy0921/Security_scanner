import json
import logging
from typing import Any

from groq import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import (
    AIProviderError,
    AIProviderRateLimitError,
    AIServiceUnavailableError,
    InvalidAIResponseError,
)
from app.schemas.detection import AIResult


_SCAM_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["scam", "not_scam", "suspicious"]},
        "confidence_score": {"type": "number"},
        "scam_type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "risk_factors": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "explanation": {"type": "string"},
    },
    "required": [
        "label",
        "confidence_score",
        "scam_type",
        "risk_factors",
        "recommendations",
        "explanation",
    ],
    "additionalProperties": False,
}

logger = logging.getLogger("app.groq")


class GroqService:
    """Calls Groq and validates model output before it enters the application."""

    def __init__(self, client: AsyncGroq, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def classify(self, messages: list[dict[str, str]]) -> AIResult:
        try:
            completion = await self.client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                temperature=0,
                max_completion_tokens=1_000,
                reasoning_format="hidden",
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "scam_detection_result",
                        "strict": True,
                        "schema": _SCAM_RESULT_SCHEMA,
                    },
                },
            )
        except RateLimitError as exc:
            logger.warning("groq_request_failed error_type=rate_limit status_code=%s", exc.status_code)
            raise AIProviderRateLimitError(
                "The analysis provider is rate limited. Please retry shortly"
            ) from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            logger.error("groq_request_failed error_type=invalid_credentials status_code=%s", exc.status_code)
            raise AIProviderError("The analysis provider rejected its server credentials") from exc
        except APITimeoutError as exc:
            logger.error("groq_request_failed error_type=timeout")
            raise AIServiceUnavailableError("The analysis service timed out. Please retry shortly") from exc
        except APIConnectionError as exc:
            logger.error("groq_request_failed error_type=connection")
            raise AIServiceUnavailableError("The analysis service is currently unavailable") from exc
        except APIStatusError as exc:
            provider_error = exc.body.get("error", exc.body) if isinstance(exc.body, dict) else {}
            provider_code = provider_error.get("code") if isinstance(provider_error, dict) else None
            provider_param = provider_error.get("param") if isinstance(provider_error, dict) else None
            logger.error(
                "groq_request_failed error_type=provider_status status_code=%s code=%s param=%s",
                exc.status_code,
                provider_code[:80] if isinstance(provider_code, str) else None,
                provider_param[:80] if isinstance(provider_param, str) else None,
            )
            if exc.status_code == 408 or exc.status_code >= 500:
                raise AIServiceUnavailableError("The analysis service is currently unavailable") from exc
            raise AIProviderError("The analysis provider rejected the request") from exc
        except APIError as exc:
            logger.error("groq_request_failed error_type=%s", type(exc).__name__)
            raise AIProviderError("The analysis provider could not process the request") from exc

        failure_stage = "read"
        finish_reason = None
        raw_content: Any = None
        try:
            choice = completion.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            raw_content = choice.message.content
            if not isinstance(raw_content, str):
                raise TypeError("Groq response content was not text")
            failure_stage = "decode"
            parsed_content = json.loads(raw_content)
            failure_stage = "validate"
            return AIResult.model_validate(parsed_content)
        except (AttributeError, IndexError, TypeError, ValueError, ValidationError) as exc:
            invalid_fields = []
            if isinstance(exc, ValidationError):
                invalid_fields = [
                    ".".join(str(part) for part in error["loc"])
                    for error in exc.errors()
                ]
            logger.warning(
                "groq_response_invalid stage=%s error_type=%s finish_reason=%s content_length=%s invalid_fields=%s",
                failure_stage,
                type(exc).__name__,
                finish_reason,
                len(raw_content) if isinstance(raw_content, str) else None,
                invalid_fields,
            )
            raise InvalidAIResponseError("The analysis service returned an invalid result") from exc
