from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.colleges import router as colleges_router
from app.api.v1.courses import router as courses_router
from app.api.v1.health import router as health_router
from app.api.v1.materials import router as materials_router
from app.api.v1.upload import router as upload_router

router = APIRouter()
router.include_router(health_router, tags=['health'])
router.include_router(auth_router, tags=['auth'])
router.include_router(colleges_router, tags=['colleges'])
router.include_router(courses_router, tags=['courses'])
router.include_router(materials_router, tags=['materials'])
router.include_router(upload_router, tags=['upload'])
