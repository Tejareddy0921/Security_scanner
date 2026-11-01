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
        "scam_type": {"type": ["string", "null"]},
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
            logger.error("groq_request_failed error_type=provider_status status_code=%s", exc.status_code)
            if exc.status_code == 408 or exc.status_code >= 500:
                raise AIServiceUnavailableError("The analysis service is currently unavailable") from exc
            raise AIProviderError("The analysis provider rejected the request") from exc
        except APIError as exc:
            logger.error("groq_request_failed error_type=%s", type(exc).__name__)
            raise AIProviderError("The analysis provider could not process the request") from exc

        try:
            raw_content: Any = completion.choices[0].message.content
            if not isinstance(raw_content, str):
                raise TypeError("Groq response content was not text")
            return AIResult.model_validate(json.loads(raw_content))
        except (AttributeError, IndexError, TypeError, ValueError, ValidationError) as exc:
            logger.warning("groq_response_invalid error_type=%s", type(exc).__name__)
            raise InvalidAIResponseError("The analysis service returned an invalid result") from exc
