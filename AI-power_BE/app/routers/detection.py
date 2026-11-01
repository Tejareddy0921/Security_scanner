from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_detection_service
from app.schemas.detection import DetectionRequest, DetectionResponse
from app.services.detection_service import DetectionService


router = APIRouter(prefix="/detection", tags=["detection"])


@router.post("/analyze", response_model=DetectionResponse, status_code=status.HTTP_201_CREATED)
async def analyze(
    request: DetectionRequest,
    user=Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> DetectionResponse:
    return await service.analyze(user, request)


@router.get("/history", response_model=list[DetectionResponse])
async def history(
    user=Depends(get_current_user), service: DetectionService = Depends(get_detection_service)
) -> list[DetectionResponse]:
    return await service.history(user)


@router.get("/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    detection_id: str,
    user=Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
) -> DetectionResponse:
    return await service.get_mine(user, detection_id)
