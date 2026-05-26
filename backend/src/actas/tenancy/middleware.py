from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_AUTH_EXEMPT = {"/auth/login", "/auth/refresh", "/auth/logout", "/healthz", "/readyz", "/docs", "/openapi.json"}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in _AUTH_EXEMPT:
            org_id = request.headers.get("X-Organization-Id")
            request.state.org_id = org_id  # may be None; deps validate
        else:
            request.state.org_id = None
        return await call_next(request)
