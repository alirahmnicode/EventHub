import math
import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.handlers import _error_response

_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        incoming = Headers(scope=scope).get("x-request-id")
        rid = incoming if incoming and _VALID_ID.match(incoming) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = rid

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = rid
                headers["X-Response-Time"] = (
                    f"{(time.perf_counter() - start) * 1000:.1f}ms"
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        limit: int = 100,
        window: int = 60,
        exempt_paths: frozenset[str] = frozenset({"/health"}),
    ):
        self.app = app
        self.limit = limit
        self.window = window
        self.exempt_paths = exempt_paths
        self.buckets: dict[str, dict] = {}  # swap for Redis later

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        rip = client[0] if client else "unknown"
        now = time.perf_counter()
        bucket = self.buckets.get(rip)

        if bucket is None or now - bucket["window_start"] > self.window:
            bucket = {"remaining": self.limit - 1, "window_start": now}
            self.buckets[rip] = bucket
        elif bucket["remaining"] > 0:
            bucket["remaining"] -= 1
        else:
            retry_after = max(
                1, math.ceil(self.window - (now - bucket["window_start"]))
            )
            response = _error_response(
                Request(scope, receive),
                429,
                "rate_limited",
                f"Too many requests. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-RateLimit-Remaining"] = str(bucket["remaining"])
            await send(message)

        await self.app(scope, receive, send_wrapper)
