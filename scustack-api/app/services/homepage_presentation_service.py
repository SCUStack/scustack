from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_config import SiteConfig

HOMEPAGE_PRESENTATION_KEY = 'homepage_presentation'

DEFAULT_HOMEPAGE_PRESENTATION = {
    'banners': [
        {'image': '/banners/b1.jpg', 'title': '知识川流不息', 'subtitle': '让每一份笔记都找到需要它的人'},
        {'image': '/banners/b2.jpg', 'title': '取之学生，用之学生', 'subtitle': '公益、开源、无广告的学习资料共享平台'},
        {'image': '/banners/b3.jpg', 'title': '共建学习社区', 'subtitle': '上传你的资料，帮助学弟学妹少走弯路'},
    ],
}


async def get_homepage_presentation(db: AsyncSession) -> dict:
    result = await db.execute(
        select(SiteConfig).where(SiteConfig.config_key == HOMEPAGE_PRESENTATION_KEY)
    )
    config = result.scalar_one_or_none()
    if config is None or not config.config_value:
        return DEFAULT_HOMEPAGE_PRESENTATION
    return {
        'banners': config.config_value.get('banners') or DEFAULT_HOMEPAGE_PRESENTATION['banners'],
    }


async def upsert_homepage_presentation(db: AsyncSession, config_value: dict, updated_by) -> SiteConfig:
    result = await db.execute(
        select(SiteConfig).where(SiteConfig.config_key == HOMEPAGE_PRESENTATION_KEY)
    )
    config = result.scalar_one_or_none()
    payload = {
        'banners': config_value.get('banners') or DEFAULT_HOMEPAGE_PRESENTATION['banners'],
    }
    if config is None:
        config = SiteConfig(
            config_key=HOMEPAGE_PRESENTATION_KEY,
            config_value=payload,
            updated_by=updated_by,
        )
        db.add(config)
    else:
        config.config_value = payload
        config.updated_by = updated_by
    await db.flush()
    return config
