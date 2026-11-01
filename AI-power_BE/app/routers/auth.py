from fastapi import APIRouter, Depends, status

from app.dependencies.services import get_auth_service
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> UserResponse:
    return await service.register(str(request.email), request.full_name, request.password)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    result = await service.login(str(request.email), request.password)
    return TokenResponse(**result)
