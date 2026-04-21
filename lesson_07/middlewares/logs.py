from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LogRequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super(LogRequestMiddleware, self).__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = perf_counter()
        print(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        response.headers["X-Response-Time"] = f"{perf_counter() - start:.2f}s"
        return response
