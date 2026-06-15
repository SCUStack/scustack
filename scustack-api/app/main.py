from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.middleware.security import SecurityHeadersMiddleware
from app.schemas.common import ErrorCode


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control headers based on request path."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if path.startswith('/api/v1/'):
            response.headers['Cache-Control'] = 'no-store'
        elif any(path.endswith(ext) for ext in ('.js', '.css', '.woff2', '.png', '.jpg', '.webp', '.svg')):
            response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
        elif path.startswith('/_nuxt/'):
            response.headers['Cache-Control'] = 'public, max-age=604800'

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title='川大课栈 API',
    description='SCU Course Stack — 公益课程资料共享平台',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['Content-Type', 'X-Requested-With'],
)
app.add_middleware(CacheControlMiddleware)


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
    return JSONResponse(
        status_code=500,
        content={
            'code': ErrorCode.INTERNAL_ERROR,
            'data': None,
            'message': 'internal server error',
            'detail': None,  # Never leak exception details
        },
    )


app.include_router(v1_router, prefix='/api/v1')
