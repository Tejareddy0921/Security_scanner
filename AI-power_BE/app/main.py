import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import get_settings
from app.core.database import lifespan
from app.core.errors import (
    AIServiceUnavailableError,
    AIProviderError,
    AIProviderRateLimitError,
    AuthenticationError,
    DependencyUnavailableError,
    DomainError,
    DuplicateResourceError,
    InvalidAIResponseError,
    InvalidInputError,
    ResourceNotFoundError,
)
from app.core.middleware import RequestLoggingMiddleware, RequestSizeLimitMiddleware
from app.routers import auth, detection, scam, users


logger = logging.getLogger("app")
settings = get_settings()
app = FastAPI(title="AI-Powered Scam Detection System", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_size_bytes)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scam.router)
app.include_router(detection.router)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    del request
    if isinstance(exc, DuplicateResourceError):
        status_code = 409
    elif isinstance(exc, AIProviderRateLimitError):
        status_code = 429
    elif isinstance(exc, AIProviderError):
        status_code = 502
    elif isinstance(exc, ResourceNotFoundError):
        status_code = 404
    elif isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, InvalidInputError):
        status_code = 400
    elif isinstance(exc, InvalidAIResponseError):
        status_code = 502
    elif isinstance(exc, (AIServiceUnavailableError, DependencyUnavailableError)):
        status_code = 503
    else:
        status_code = 500
    return JSONResponse({"detail": str(exc)}, status_code=status_code)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    logger.warning(
        "request_validation_failed method=%s path=%s fields=%s",
        request.method,
        request.url.path,
        [{"loc": error["loc"], "type": error["type"]} for error in errors],
    )
    return JSONResponse({"detail": errors}, status_code=422)


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
    del request, exc
    return JSONResponse({"detail": "A resource with these values already exists"}, status_code=409)


@app.exception_handler(PyMongoError)
async def database_error_handler(request: Request, exc: PyMongoError) -> JSONResponse:
    logger.error(
        "database_operation_failed method=%s path=%s error_type=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse({"detail": "Database service is currently unavailable"}, status_code=503)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "AI-Powered Scam Detection System"}
