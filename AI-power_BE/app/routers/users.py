from fastapi import APIRouter, Depends, Response, status

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_user_service
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user), service: UserService = Depends(get_user_service)) -> UserResponse:
    return await service.get_me(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.update_me(user, request)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user=Depends(get_current_user), service: UserService = Depends(get_user_service)) -> Response:
    await service.deactivate(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
