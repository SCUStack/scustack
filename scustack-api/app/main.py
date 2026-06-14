from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.schemas.common import ErrorCode


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title='川大课栈 API',
    description='SCU Course Stack — 公益课程资料共享平台',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            'code': ErrorCode.INTERNAL_ERROR,
            'data': None,
            'message': 'internal server error',
            'detail': str(exc) if settings.DEBUG else None,
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


app.include_router(v1_router, prefix='/api/v1')
