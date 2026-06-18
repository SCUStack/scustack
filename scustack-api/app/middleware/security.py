from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        if request.url.scheme == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        script_src = ["'self'", 'https://cdn.jsdelivr.net']
        style_src = ["'self'", 'https://fonts.googleapis.com', 'https://cdn.jsdelivr.net']
        frame_src = ["'self'"]

        if settings.APP_ENV == 'dev':
            script_src.insert(1, "'unsafe-inline'")
            style_src.insert(1, "'unsafe-inline'")
            frame_src.append('http://localhost:*')

        csp = (
            "default-src 'self'; "
            f"script-src {' '.join(script_src)}; "
            f"style-src {' '.join(style_src)}; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            f"frame-src {' '.join(frame_src)}; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        return response
