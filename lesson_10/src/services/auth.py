"""JWT (lesson_09) + RBAC (тема 10)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.entity.models import UserRole
from src.repository.refresh_tokens import RefreshTokenRepository
from src.repository.users import UserRepository
from src.schemas.auth import CurrentUser, TokenPair
from src.schemas.user import UserCreate


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hash = PasswordHash.recommended()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user: CurrentUser) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role.value,
        "type": "access",
        "exp": expires_at,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        user_id = payload.get("user_id")
        role_value = payload.get("role")
        token_type = payload.get("type")
        if (
            not isinstance(username, str)
            or not isinstance(user_id, int)
            or not isinstance(role_value, str)
            or token_type != "access"
        ):
            raise credentials_error
        role = UserRole(role_value)
    except (InvalidTokenError, ValueError):
        raise credentials_error

    return CurrentUser(id=user_id, username=username, role=role)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    return decode_access_token(token)


async def get_current_moderator_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав доступу",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав доступу",
        )
    return current_user


class AuthService:
    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    async def register(self, body: UserCreate):
        existing_user = await self.users.get_by_username_or_email(
            body.username, str(body.email)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            )

        return await self.users.create_user(body, hash_password(body.password))

    async def login(self, username: str, password: str) -> TokenPair:
        user = await self.users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await self.create_token_pair(CurrentUser.model_validate(user))

    async def create_token_pair(self, user: CurrentUser) -> TokenPair:
        refresh_token = secrets.token_urlsafe(64)
        expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_tokens.create_token(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
        return TokenPair(
            access_token=create_access_token(user),
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        saved_token = await self.refresh_tokens.get_by_hash(hash_token(refresh_token))
        if saved_token is None or saved_token.expires_at < utc_now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await self.users.get_by_id(saved_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return create_access_token(CurrentUser.model_validate(user))

    async def logout(self, refresh_token: str, current_user: CurrentUser) -> None:
        saved_token = await self.refresh_tokens.get_by_hash(hash_token(refresh_token))
        if saved_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        if saved_token.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Refresh token does not belong to this user",
            )
        await self.refresh_tokens.delete_by_hash(hash_token(refresh_token))


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthService:
    return AuthService(db)
