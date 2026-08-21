import time
from collections import defaultdict, deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

LIMIT = 50
WINDOW_SECONDS = 60

# client_ip -> deque of request timestamps within the current window.
# TODO: unbounded growth, per-process only — fine for now, revisit if this
# becomes long-running under real traffic without a restart.
request_log: dict[str, deque] = defaultdict(deque)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._client_ip(scope)
        now = time.monotonic()
        timestamps = request_log[client_ip]

        self._evict_old(timestamps, now)

        if len(timestamps) >= LIMIT:
            retry_after = int(WINDOW_SECONDS - (now - timestamps[0])) + 1
            response = self._too_many_requests(retry_after)
            await response(scope, receive, send)
            return

        timestamps.append(now)
        await self.app(scope, receive, send)

    def _client_ip(self, scope: Scope) -> str:
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _evict_old(self, timestamps: deque, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()

    def _too_many_requests(self, retry_after: int) -> JSONResponse:
        return JSONResponse(
            {"detail": f"Too many requests. Try again in {retry_after} seconds."},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
