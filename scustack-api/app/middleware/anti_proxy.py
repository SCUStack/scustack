from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

ALLOWED_HOSTS = {'scustack.com', 'www.scustack.com', 'localhost', '127.0.0.1'}


class AntiProxyMiddleware(BaseHTTPMiddleware):
    """Block cross-origin API requests to prevent unauthorized proxy/mirroring."""

    async def dispatch(self, request: Request, call_next):
        if settings.is_dev:
            return await call_next(request)
        if not request.url.path.startswith('/api/'):
            return await call_next(request)

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('Origin', '')
            if origin:
                try:
                    from urllib.parse import urlparse
                    host = urlparse(origin).hostname or ''
                    if host and not _is_allowed_host(host):
                        return JSONResponse(
                            {'code': 40300, 'data': None, 'message': 'forbidden'},
                            status_code=403,
                        )
                except Exception:
                    pass
            return await call_next(request)

        # For state-changing requests, enforce Origin check
        origin = request.headers.get('Origin', '')
        referer = request.headers.get('Referer', '')

        if origin or referer:
            host = ''
            if origin:
                try:
                    from urllib.parse import urlparse
                    host = urlparse(origin).hostname or ''
                except Exception:
                    pass
            if not host and referer:
                try:
                    from urllib.parse import urlparse
                    host = urlparse(referer).hostname or ''
                except Exception:
                    pass
            if host and not _is_allowed_host(host):
                return JSONResponse(
                    {'code': 40300, 'data': None, 'message': 'cross-origin requests not allowed'},
                    status_code=403,
                )

        return await call_next(request)


def _is_allowed_host(host: str) -> bool:
    if host in ALLOWED_HOSTS:
        return True
    if settings.is_dev and host in ('localhost', '127.0.0.1', '0.0.0.0'):
        return True
    return False
