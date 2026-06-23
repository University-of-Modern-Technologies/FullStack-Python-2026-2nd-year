"""HTTP-маршрути автентифікації, токенів і підтвердження email."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from src.conf.config import settings

from src.schemas.auth import (
    AccessToken,
    CurrentUser,
    RefreshTokenRequest,
    ResendVerificationRequest,
    TokenPair,
)
from src.schemas.user import UserCreate, UserResponse
from src.services.auth import AuthService, get_auth_service, get_current_user
from src.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=settings.templates_dir)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Реєструє нового користувача після перевірки унікальності."""
    user = await auth_service.register(body)
    background_tasks.add_task(
        send_verification_email, user.id, user.email, user.username
    )
    return user


@router.post("/login", response_model=TokenPair)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Перевіряє credentials і повертає пару JWT/refresh токенів."""
    return await auth_service.login(form_data.username, form_data.password)


@router.get("/verify-email")
async def verify_email(
    request: Request,
    token: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Підтверджує email за verification token."""
    already_verified = await auth_service.verify_email(token)
    if already_verified:
        title = "Email вже підтверджено"
        message = "Цей email уже було підтверджено. Можете увійти в застосунок."
    else:
        title = "Email підтверджено"
        message = "Email успішно підтверджено. Можете увійти в застосунок."
    return templates.TemplateResponse(
        request,
        "pages/verify_email_result.html",
        {
            "title": title,
            "message": message,
            "already_verified": already_verified,
        },
    )


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    body: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Повертає користувача для повторного листа підтвердження."""
    user = await auth_service.resend_verification(str(body.email))
    if user is not None:
        background_tasks.add_task(
            send_verification_email,
            user.id,
            user.email,
            user.username,
        )
    return None


@router.post("/refresh", response_model=AccessToken)
async def refresh_token(
    body: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Виконує операцію refresh_token у модулі auth."""
    access_token = await auth_service.refresh_access_token(body.refresh_token)
    return AccessToken(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Видаляє refresh-токен поточного користувача."""
    await auth_service.logout(body.refresh_token, current_user)
    return None
