import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from starlette.responses import JSONResponse


logger = logging.getLogger("app")


class RequestLoggingMiddleware:
    """Log request metadata without reading or buffering request bodies."""

    def __init__(self, app: Callable[..., Awaitable[Any]]) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4().hex
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-request-id", request_id.encode("ascii")),
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "request_completed request_id=%s method=%s path=%s status=%d duration_ms=%.2f",
                request_id,
                scope.get("method", ""),
                scope.get("path", ""),
                status_code,
                elapsed_ms,
            )


class RequestSizeLimitMiddleware:
    """Reject oversized declared request bodies without consuming the ASGI stream."""

    def __init__(self, app: Callable[..., Awaitable[Any]], max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_lengths = [value for key, value in scope.get("headers", []) if key.lower() == b"content-length"]
        if content_lengths:
            if len(content_lengths) != 1 or not content_lengths[0].isdigit():
                response = JSONResponse({"detail": "Invalid Content-Length header"}, status_code=400)
                await response(scope, receive, send)
                return
            if int(content_lengths[0]) > self.max_bytes:
                response = JSONResponse({"detail": "Request body is too large"}, status_code=413)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
