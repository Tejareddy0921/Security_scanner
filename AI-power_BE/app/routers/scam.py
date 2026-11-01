from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_scam_service
from app.schemas.scam import ScamReportCreate, ScamReportResponse
from app.services.scam_service import ScamService


router = APIRouter(prefix="/scams", tags=["scam reports"])


@router.post("/report", response_model=ScamReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ScamReportCreate,
    user=Depends(get_current_user),
    service: ScamService = Depends(get_scam_service),
) -> ScamReportResponse:
    return await service.create(user, request)


@router.get("/my-reports", response_model=list[ScamReportResponse])
async def list_reports(
    user=Depends(get_current_user), service: ScamService = Depends(get_scam_service)
) -> list[ScamReportResponse]:
    return await service.list_mine(user)


@router.get("/{report_id}", response_model=ScamReportResponse)
async def get_report(
    report_id: str,
    user=Depends(get_current_user),
    service: ScamService = Depends(get_scam_service),
) -> ScamReportResponse:
    return await service.get_mine(user, report_id)
