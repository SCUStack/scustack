import asyncio

from sqlalchemy import select

from app.core import elasticsearch as es
from app.core.database import async_session
from app.models.material import Material
from app.tasks.content_extract import build_index_document


async def rebuild() -> None:
    await es.ensure_materials_index()
    async with async_session() as db:
        materials = (
            await db.scalars(
                select(Material).where(Material.review_status == 'approved')
            )
        ).all()
        for material in materials:
            document = await build_index_document(db, material)
            await es.index_material(str(material.id), document)
    if es.es is not None:
        await es.es.close()
    print(f'Indexed {len(materials)} approved materials')


if __name__ == '__main__':
    asyncio.run(rebuild())
