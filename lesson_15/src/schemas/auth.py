"""Pydantic-схеми для автентифікації та токенів."""
from pydantic import BaseModel, ConfigDict, EmailStr

from src.entity.models import UserRole


class CurrentUser(BaseModel):
    """Дані користувача, витягнуті з валідного access JWT."""
    id: int
    username: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class TokenPair(BaseModel):
    """Пара access і refresh токенів."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    """Відповідь з новим access-токеном."""
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Тіло запиту, що містить refresh-токен."""
    refresh_token: str


class ResendVerificationRequest(BaseModel):
    """Тіло запиту на повторну відправку email-підтвердження."""
    email: EmailStr
