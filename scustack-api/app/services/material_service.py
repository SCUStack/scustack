from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from difflib import unified_diff

import httpx

from app.core import oss
from app.models.material import Material, MaterialVersion

TEXT_EXTENSIONS = {
    'txt', 'md', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'hpp',
    'css', 'html', 'xml', 'json', 'yaml', 'yml', 'toml',
    'ini', 'cfg', 'sh', 'bash', 'sql', 'r', 'go', 'rs', 'swift',
    'kt', 'rb', 'php', 'pl', 'lua', 'vue', 'svelte', 'jsx', 'tsx',
    'csv', 'log', 'tex', 'sty',
}


async def list_materials(db: AsyncSession, course_id: UUID | None = None,
                         category: str | None = None, semester: str | None = None,
                         review_status: str = 'approved', limit: int = 20,
                         offset: int = 0) -> list[Material]:
    stmt = select(Material).where(Material.review_status == review_status)
    if course_id:
        stmt = stmt.where(Material.course_id == course_id)
    if category:
        stmt = stmt.where(Material.category == category)
    if semester:
        stmt = stmt.where(Material.semester == semester)
    stmt = stmt.order_by(Material.is_pinned.desc(), Material.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_material(db: AsyncSession, material_id: UUID) -> Material | None:
    result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    return result.scalar_one_or_none()


async def create_material(db: AsyncSession, user_id: UUID, **kwargs) -> Material:
    kwargs.setdefault('contributor_id', user_id)
    material = Material(**kwargs)
    db.add(material)
    await db.flush()

    if kwargs.get('storage_key') and kwargs.get('file_hash'):
        v = MaterialVersion(
            material_id=material.id,
            version_number=1,
            file_hash=kwargs['file_hash'],
            storage_key=kwargs['storage_key'],
            file_size=kwargs.get('file_size', 0),
            uploaded_by=user_id,
        )
        db.add(v)
        await db.flush()

    return material


async def update_material(db: AsyncSession, material_id: UUID, user_id: UUID,
                          role: str, **kwargs) -> Material | None:
    material = await get_material(db, material_id)
    if material is None:
        return None
    if str(material.contributor_id) != str(user_id) and role not in ('maintainer', 'admin'):
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(material, k, v)
    await db.flush()
    return material


async def soft_delete_material(db: AsyncSession, material_id: UUID, user_id: UUID,
                               role: str) -> bool:
    material = await get_material(db, material_id)
    if material is None:
        return False
    if str(material.contributor_id) != str(user_id) and role not in ('maintainer', 'admin'):
        return False
    material.review_status = 'removed'
    await db.flush()
    return True


async def get_latest_version(db: AsyncSession, material_id: UUID) -> MaterialVersion | None:
    result = await db.execute(
        select(MaterialVersion).where(MaterialVersion.material_id == material_id)
        .order_by(MaterialVersion.version_number.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def add_version(db: AsyncSession, material_id: UUID, user_id: UUID,
                      storage_key: str, file_hash: str, file_size: int,
                      change_note: str | None = None) -> MaterialVersion | None:
    material = await get_material(db, material_id)
    if material is None:
        return None

    result = await db.execute(
        select(MaterialVersion).where(MaterialVersion.material_id == material_id)
        .order_by(MaterialVersion.version_number.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    next_num = (latest.version_number + 1) if latest else 1

    v = MaterialVersion(
        material_id=material_id,
        version_number=next_num,
        file_hash=file_hash,
        storage_key=storage_key,
        file_size=file_size,
        change_note=change_note,
        uploaded_by=user_id,
    )
    material.file_hash = file_hash
    material.file_size = file_size
    material.trust_status = 'unverified'
    db.add(v)
    await db.flush()
    return v


async def rate_material(db: AsyncSession, material_id: UUID, user_id: UUID, score: int) -> None:
    if score < 1 or score > 5:
        raise ValueError('score must be between 1 and 5')

    from app.models.user import User
    from app.models.material import Material
    from sqlalchemy import and_

    # Check existing rating
    from app.models.material import Material  # noqa: F811
    # Use raw SQL to upsert
    from sqlalchemy import text
    await db.execute(
        text("""
            INSERT INTO ratings (material_id, user_id, score, created_at)
            VALUES (:mid, :uid, :score, NOW())
            ON CONFLICT (material_id, user_id) DO UPDATE SET score = :score, created_at = NOW()
        """),
        {'mid': material_id, 'uid': user_id, 'score': score},
    )

    # Recalculate average
    result = await db.execute(
        text('SELECT AVG(score)::numeric(3,2), COUNT(*) FROM ratings WHERE material_id = :mid'),
        {'mid': material_id},
    )
    row = result.fetchone()
    avg_val, cnt = row

    m = await get_material(db, material_id)
    if m:
        m.average_rating = float(avg_val) if avg_val else 0
        m.rating_count = cnt


async def list_versions(db: AsyncSession, material_id: UUID) -> list[MaterialVersion]:
    result = await db.execute(
        select(MaterialVersion).where(MaterialVersion.material_id == material_id)
        .order_by(MaterialVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def get_version_diff(db: AsyncSession, material_id: UUID, version_id: UUID) -> dict:
    target = await db.execute(
        select(MaterialVersion).where(MaterialVersion.id == version_id, MaterialVersion.material_id == material_id)
    )
    target_v = target.scalar_one_or_none()
    if not target_v:
        raise ValueError('version not found')

    prev = await db.execute(
        select(MaterialVersion).where(
            MaterialVersion.material_id == material_id,
            MaterialVersion.version_number == target_v.version_number - 1,
        )
    )
    prev_v = prev.scalar_one_or_none()

    ext = target_v.storage_key.rsplit('.', 1)[-1].lower() if '.' in target_v.storage_key else ''
    if ext not in TEXT_EXTENSIONS:
        return {
            'version_id': str(target_v.id),
            'version_number': target_v.version_number,
            'change_note': target_v.change_note,
            'diff': None,
            'message': 'diff available for text files only',
        }

    old_content = ''
    new_content = ''
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if prev_v:
                old_url = oss.generate_download_url(prev_v.storage_key)
                resp = await client.get(old_url)
                if resp.status_code == 200:
                    old_content = resp.text
            new_url = oss.generate_download_url(target_v.storage_key)
            resp = await client.get(new_url)
            if resp.status_code == 200:
                new_content = resp.text
    except Exception:
        return {
            'version_id': str(target_v.id),
            'version_number': target_v.version_number,
            'change_note': target_v.change_note,
            'diff': None,
            'message': 'failed to retrieve file content for diff',
        }

    old_label = f'v{prev_v.version_number}' if prev_v else '(empty)'
    new_label = f'v{target_v.version_number}'
    diff_lines = list(unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=old_label, tofile=new_label,
    ))

    return {
        'version_id': str(target_v.id),
        'version_number': target_v.version_number,
        'change_note': target_v.change_note,
        'diff': diff_lines[:500],
        'truncated': len(diff_lines) > 500,
        'message': f'comparing {old_label} → {new_label}',
    }


async def get_related(db: AsyncSession, course_id: UUID, exclude_id: UUID, limit: int = 3) -> list[Material]:
    result = await db.execute(
        select(Material).where(
            Material.course_id == course_id,
            Material.id != exclude_id,
            Material.review_status == 'approved',
        ).order_by(Material.download_count.desc()).limit(limit)
    )
    return list(result.scalars().all())
