from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from src.conf.config import settings
from src.limiter import limiter
from src.schemas.auth import CurrentUser
from src.schemas.user import UserResponse
from src.services.auth import get_current_user
from src.services.users import UsersService, get_users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    description="Rate limit",
)
@limiter.limit(settings.RATE_LIMIT_ME)
async def me(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    users_service: Annotated[UsersService, Depends(get_users_service)],
):
    return await users_service.get_me(current_user.id)


@router.patch("/me/avatar", response_model=UserResponse)
async def update_avatar(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    users_service: Annotated[UsersService, Depends(get_users_service)],
    file: UploadFile = File(...),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only image files are allowed",
        )
    file_bytes = await file.read()
    return await users_service.update_avatar(current_user.id, file_bytes)
