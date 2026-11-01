from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

user_service = UserService()


@router.get(
    "/me",
    response_model=UserResponse
)
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the currently authenticated user's profile.
    """

    return await user_service.get_user_by_id(
        str(current_user["_id"])
    )


@router.put(
    "/me",
    response_model=UserResponse
)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the currently authenticated user's profile.
    """

    try:
        updated_user = await user_service.update_user(
            str(current_user["_id"]),
            user_data
        )

        return updated_user

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_account(
    current_user: dict = Depends(get_current_user)
):
    """
    Delete the currently authenticated user's account.
    """

    try:
        await user_service.delete_user(
            str(current_user["_id"])
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )