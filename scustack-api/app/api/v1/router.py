from fastapi import APIRouter

from app.api.v1.about import router as about_router
from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bookmarks import router as bookmarks_router
from app.api.v1.colleges import router as colleges_router
from app.api.v1.corrections import router as corrections_router
from app.api.v1.courses import router as courses_router
from app.api.v1.health import router as health_router
from app.api.v1.homepage import router as homepage_router
from app.api.v1.materials import router as materials_router
from app.api.v1.search import router as search_router
from app.api.v1.upload import router as upload_router
from app.api.v1.users import router as users_router

router = APIRouter()
router.include_router(health_router, tags=['health'])
router.include_router(auth_router, tags=['auth'])
router.include_router(users_router, tags=['users'])
router.include_router(colleges_router, tags=['colleges'])
router.include_router(courses_router, tags=['courses'])
router.include_router(materials_router, tags=['materials'])
router.include_router(bookmarks_router, tags=['bookmarks'])
router.include_router(upload_router, tags=['upload'])
router.include_router(search_router, tags=['search'])
router.include_router(homepage_router, tags=['homepage'])
router.include_router(about_router, tags=['about'])
router.include_router(corrections_router, tags=['corrections'])
router.include_router(admin_router, tags=['admin'])
