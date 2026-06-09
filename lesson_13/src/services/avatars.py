"""Сервіс завантаження аватарів у Cloudinary."""
import asyncio
import logging

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")

cloudinary.config(
    cloud_name=settings.CLD_NAME,
    api_key=settings.CLD_API_KEY,
    api_secret=settings.CLD_API_SECRET,
    secure=True,
)


async def upload_avatar(file_bytes: bytes, user_id: int) -> str:
    """Завантажує байти аватара у Cloudinary і повертає secure URL."""
    folder = "avatars"
    public_id = f"user_{user_id}"
    try:
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            file_bytes,
            folder=folder,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
        )
    except Exception as err:
        logger.error("Cloudinary upload failed for user_id=%s: %s", user_id, err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload avatar",
        ) from err

    return cloudinary.CloudinaryImage(f"{folder}/{public_id}").build_url(
        width=250,
        height=250,
        crop="fill",
        version=result.get("version"),
    )
