import pytest
from fastapi import HTTPException, status

from src.services.avatars import upload_avatar


@pytest.mark.asyncio
async def test_upload_avatar_returns_cloudinary_url(monkeypatch):
    upload_calls = []

    def fake_upload(file_bytes: bytes, **kwargs):
        upload_calls.append((file_bytes, kwargs))
        return {"version": 12345}

    class FakeCloudinaryImage:
        def __init__(self, public_id: str):
            self.public_id = public_id

        def build_url(self, **kwargs):
            assert self.public_id == "avatars/user_42"
            assert kwargs == {
                "width": 250,
                "height": 250,
                "crop": "fill",
                "version": 12345,
            }
            return "https://res.cloudinary.test/avatars/user_42.png"

    monkeypatch.setattr("src.services.avatars.cloudinary.uploader.upload", fake_upload)
    monkeypatch.setattr("src.services.avatars.cloudinary.CloudinaryImage", FakeCloudinaryImage)

    result = await upload_avatar(b"image-bytes", user_id=42)

    assert result == "https://res.cloudinary.test/avatars/user_42.png"
    assert upload_calls == [
        (
            b"image-bytes",
            {
                "folder": "avatars",
                "public_id": "user_42",
                "overwrite": True,
                "resource_type": "image",
            },
        )
    ]


@pytest.mark.asyncio
async def test_upload_avatar_raises_502_when_cloudinary_fails(monkeypatch):
    def fake_upload(*_args, **_kwargs):
        raise RuntimeError("cloudinary unavailable")

    monkeypatch.setattr("src.services.avatars.cloudinary.uploader.upload", fake_upload)

    with pytest.raises(HTTPException) as exc_info:
        await upload_avatar(b"image-bytes", user_id=42)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc_info.value.detail == "Failed to upload avatar"
