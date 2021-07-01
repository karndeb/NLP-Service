import structlog
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from starlette_context import context, plugins
from starlette_context.middleware import RawContextMiddleware, ContextMiddleware

logger = structlog.get_logger("starlette_context_example")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Example logging middleware."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        await logger.info("request log", request=request)
        response = await call_next(request)
        await logger.info("response log", response=response)
        print(response.headers.items())
        return response


# class YourMiddleware(ContextMiddleware):
#     async def set_context(self, request: Request) -> dict:
#         return {"from_middleware": True}



# Commit changes before returning the request's response
# class AutoCommitMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         response = await call_next(request)
#         Session.commit()
#         Session.remove()
#         return response