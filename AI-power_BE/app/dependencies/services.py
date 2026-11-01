from fastapi import Depends, Request

from app.ai.classifier import ScamClassifier
from app.ai.groq_service import GroqService
from app.core.config import get_settings
from app.core.database import ensure_indexes, get_database
from app.repositories.detection_repository import DetectionRepository
from app.repositories.scam_repository import ScamRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.detection_service import DetectionService
from app.services.scam_service import ScamService
from app.services.user_service import UserService


async def get_auth_service(request: Request, database=Depends(get_database)) -> AuthService:
    await ensure_indexes(request, database)
    return AuthService(UserRepository(database["users"]))


async def get_user_service(database=Depends(get_database)) -> UserService:
    return UserService(UserRepository(database["users"]))


async def get_scam_service(database=Depends(get_database)) -> ScamService:
    return ScamService(ScamRepository(database["scam_reports"]))


async def get_detection_service(request: Request, database=Depends(get_database)) -> DetectionService:
    settings = get_settings()
    client = getattr(request.app.state, "groq_client", None)
    classifier = ScamClassifier(GroqService(client, settings)) if client is not None else None
    return DetectionService(
        ScamRepository(database["scam_reports"]),
        DetectionRepository(database["detection_results"]),
        classifier,
        settings,
    )
