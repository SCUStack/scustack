from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'
CSRF_COOKIE = 'csrf_token'
CSRF_HEADER = 'X-CSRF-Token'
STATE_CHANGING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith('/api/'):
            return await call_next(request)

        if request.method not in STATE_CHANGING_METHODS:
            return await call_next(request)

        has_auth_cookie = bool(
            request.cookies.get(ACCESS_COOKIE) or request.cookies.get(REFRESH_COOKIE),
        )
        if not has_auth_cookie:
            return await call_next(request)

        csrf_cookie = request.cookies.get(CSRF_COOKIE)
        csrf_header = request.headers.get(CSRF_HEADER)

        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(
                {'code': 40300, 'data': None, 'message': 'csrf token missing or invalid'},
                status_code=403,
            )

        return await call_next(request)
