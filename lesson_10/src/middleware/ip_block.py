import json
import logging
from pathlib import Path

from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


class BlockedIpEntry(BaseModel):
    ip: str
    reason: str


def load_blocked_ips(path: Path) -> dict[str, str]:
    if not path.is_file():
        logger.warning("Blocked IPs file not found: %s", path)
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in blocked IPs file: %s", path)
        return {}

    if not isinstance(raw, list):
        logger.error("Blocked IPs file must be a JSON array: %s", path)
        return {}

    blocked: dict[str, str] = {}
    for item in raw:
        try:
            entry = BlockedIpEntry.model_validate(item)
        except ValidationError:
            logger.warning("Skip invalid blocked IP entry: %s", item)
            continue
        blocked[entry.ip] = entry.reason

    return blocked


class IpBlockMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, blocked_ips_path: Path):
        super().__init__(app)
        self._path = blocked_ips_path
        self._blocked = load_blocked_ips(blocked_ips_path)

    async def dispatch(self, request: Request, call_next):
        client = request.client
        ip = client.host if client else None

        if ip and ip in self._blocked:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "IP заблоковано",
                    "ip": ip,
                    "reason": self._blocked[ip],
                },
            )

        return await call_next(request)
