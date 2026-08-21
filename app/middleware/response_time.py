import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

RESPONSE_TIME_HEADER = "X-Response-Time"


class ResponseTimeMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                elapsed_ms = (time.perf_counter() - start) * 1000
                headers = MutableHeaders(scope=message)
                headers.append(RESPONSE_TIME_HEADER, f"{elapsed_ms:.2f}ms")
                # Stash it somewhere the Prometheus hook can read later
                scope["state"]["response_time_ms"] = elapsed_ms
            await send(message)

        await self.app(scope, receive, send_wrapper)
