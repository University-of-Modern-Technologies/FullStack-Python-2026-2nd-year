"""Сервіс відправлення листів підтвердження email."""
import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors

from src.conf.config import settings
from src.services.auth import create_verification_token

logger = logging.getLogger("uvicorn.error")

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,  # noqa
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
    TEMPLATE_FOLDER=settings.template_folder,
)

fast_mail = FastMail(mail_config)


async def send_verification_email(user_id: int, to: str, username: str) -> None:
    """Надсилає HTML-лист із посиланням для підтвердження email."""
    try:
        token = create_verification_token(user_id)
        verify_url = f"{settings.APP_PUBLIC_URL}/api/auth/verify-email?token={token}"
        message = MessageSchema(
            subject="Підтвердіть email",
            recipients=[to],
            template_body={
                "username": username,
                "verify_url": verify_url,
                "expire_hours": settings.EMAIL_VERIFY_EXPIRE_HOURS,
            },
            subtype=MessageType.html,
        )
        await fast_mail.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        logger.error("Failed to send verification email to %s: %s", to, err)
