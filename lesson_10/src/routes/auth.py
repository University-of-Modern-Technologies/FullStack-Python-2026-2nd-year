from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.conf.config import settings
from src.limiter import limiter
from src.schemas.auth import (
    AccessToken,
    CurrentUser,
    RefreshTokenRequest,
    TokenPair,
)
from src.schemas.user import UserCreate, UserResponse
from src.services.auth import AuthService, get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.register(body)


@router.post("/login", response_model=TokenPair)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth_service.login(form_data.username, form_data.password)


@router.post("/refresh", response_model=AccessToken)
async def refresh_token(
    body: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    access_token = await auth_service.refresh_access_token(body.refresh_token)
    return AccessToken(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.logout(body.refresh_token, current_user)
    return None


@router.get(
    "/me",
    response_model=CurrentUser,
    description="Rate limit",
)
@limiter.limit(settings.RATE_LIMIT_ME)
async def me(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return current_user
