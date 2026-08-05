from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.observability import CostObservabilityMiddleware
from app.middleware.anti_proxy import AntiProxyMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.ddos_protection import DDoSProtectionMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.schemas.common import ErrorCode


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control headers based on request path."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        has_explicit_cache_control = 'Cache-Control' in response.headers

        if path.startswith('/api/v1/') and not has_explicit_cache_control:
            response.headers['Cache-Control'] = 'no-store'
        elif any(path.endswith(ext) for ext in ('.js', '.css', '.woff2', '.png', '.jpg', '.webp', '.svg')):
            response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
        elif path.startswith('/_nuxt/'):
            response.headers['Cache-Control'] = 'public, max-age=604800'

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.sentry import init_sentry
    init_sentry()
    yield


app = FastAPI(
    title='川流课栈 API',
    description='SCU Course Stack — 公益课程资料共享平台',
    version='0.1.0',
    lifespan=lifespan,
    docs_url='/docs' if settings.is_dev else None,
    redoc_url='/redoc' if settings.is_dev else None,
    openapi_url='/openapi.json' if settings.is_dev else None,
)

if settings.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(DDoSProtectionMiddleware)
app.add_middleware(AntiProxyMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['Content-Type', 'X-Requested-With', 'X-CSRF-Token'],
)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(CostObservabilityMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'code': ErrorCode.BAD_REQUEST if exc.status_code == 400 else exc.status_code,
            'data': None,
            'message': exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    detail = errors[0].get('msg', 'validation error') if errors else 'validation error'
    return JSONResponse(
        status_code=422,
        content={
            'code': ErrorCode.VALIDATION_ERROR,
            'data': None,
            'message': 'request validation failed',
            'detail': detail,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            'code': ErrorCode.BAD_REQUEST,
            'data': None,
            'message': str(exc),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from app.core.sentry import capture_exception
    capture_exception(exc)

    if settings.DEBUG:
        import traceback
        traceback.print_exc()
    else:
        import logging
        logging.getLogger('scustack').error('Unhandled exception: %s %s', type(exc).__name__, str(exc)[:200])
    return JSONResponse(
        status_code=500,
        content={
            'code': ErrorCode.INTERNAL_ERROR,
            'data': None,
            'message': 'internal server error',
            'detail': str(exc) if settings.DEBUG else None,
        },
    )


if not settings.is_dev:
    issues = settings.validate_secrets()
    if issues:
        import sys, logging
        for issue in issues:
            logging.getLogger('scustack').critical('SECURITY: %s', issue)
        if settings.APP_ENV == 'prod':
            raise RuntimeError(f'Refusing to start in production with insecure defaults: {issues}')



app.include_router(v1_router, prefix='/api/v1')
