import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from groq import AsyncGroq
from fastapi import FastAPI, Request
from pymongo import AsyncMongoClient

from app.core.config import Settings, get_settings
from app.core.errors import DependencyUnavailableError


def create_groq_client(settings: Settings) -> AsyncGroq | None:
    api_key = settings.groq_api_key.get_secret_value() if settings.groq_api_key else None
    if not api_key or not api_key.strip():
        return None
    return AsyncGroq(api_key=api_key, timeout=settings.groq_timeout_seconds, max_retries=0)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    app.state.mongo_client = client
    app.state.database = client[settings.database_name]
    app.state.groq_client = create_groq_client(settings)
    app.state.indexes_ready = False
    app.state.indexes_lock = asyncio.Lock()
    try:
        yield
    finally:
        if app.state.groq_client is not None:
            await app.state.groq_client.close()
        await client.close()


async def initialize_indexes(database: Any) -> None:
    await database["users"].create_index("email", unique=True, name="users_email_unique")
    await database["scam_reports"].create_index("user_id", name="scam_reports_user_id")
    await database["scam_reports"].create_index("created_at", name="scam_reports_created_at")
    await database["detection_results"].create_index("user_id", name="detection_results_user_id")
    await database["detection_results"].create_index("report_id", name="detection_results_report_id")


async def ensure_indexes(request: Request, database: Any) -> None:
    if not request.app.state.indexes_ready:
        async with request.app.state.indexes_lock:
            if not request.app.state.indexes_ready:
                await initialize_indexes(database)
                request.app.state.indexes_ready = True


async def get_database(request: Request) -> Any:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise DependencyUnavailableError("Database is not initialized")
    return database
