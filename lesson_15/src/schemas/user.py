"""Pydantic-схеми користувачів і зміни ролі."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.entity.models import UserRole


class UserCreate(BaseModel):
    """Схема реєстрації нового користувача."""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    """Схема відповіді API з даними користувача."""
    id: int
    username: str
    email: EmailStr
    role: UserRole
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """Схема адміністративної зміни ролі користувача."""
    role: UserRole
