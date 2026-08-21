import uuid
from contextvars import ContextVar

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> str:
    return request_id_ctx.get()


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Propagate an incoming ID if present (from an upstream service/gateway),
        # otherwise generate one.
        headers = dict(scope["headers"])
        incoming = headers.get(REQUEST_ID_HEADER.lower().encode(), b"").decode()
        request_id = incoming or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                mutable_headers = MutableHeaders(scope=message)
                mutable_headers.append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_ctx.reset(token)
