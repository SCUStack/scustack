from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.models.course import Course
from app.models.material import Material
from app.models.notification import Notification
from app.models.user import RefreshToken, User


def get_masked_university_id(user: User) -> str | None:
    if not user.university_id:
        return None
    from app.core.security import decrypt_pii

    university_id = decrypt_pii(user.university_id)
    return f'{university_id[:4]}****{university_id[-4:]}'


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_profile(db: AsyncSession, user_id: UUID, **kwargs) -> User | None:
    user = await get_user(db, user_id)
    if user is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(user, k, v)
    await db.flush()
    await db.refresh(user, attribute_names=['updated_at'])
    return user


async def get_user_contributions(
    db: AsyncSession, user_id: UUID, limit: int = 20, offset: int = 0
) -> list[Material]:
    result = await db.execute(
        select(Material)
        .where(Material.contributor_id == user_id)
        .order_by(Material.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_contribution_count(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count(Material.id)).where(Material.contributor_id == user_id)
    )
    return result.scalar() or 0


async def toggle_bookmark(
    db: AsyncSession, user_id: UUID, course_id: UUID | None, material_id: UUID | None
) -> dict:
    if course_id:
        existing = await db.execute(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.course_id == course_id)
        )
        bookmark = existing.scalar_one_or_none()
    elif material_id:
        existing = await db.execute(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.material_id == material_id)
        )
        bookmark = existing.scalar_one_or_none()
    else:
        raise ValueError('course_id or material_id required')

    if bookmark:
        await db.delete(bookmark)
        await db.flush()
        return {'action': 'removed', 'bookmark_id': str(bookmark.id)}
    else:
        bookmark = Bookmark(user_id=user_id, course_id=course_id, material_id=material_id)
        db.add(bookmark)
        await db.flush()
        return {'action': 'created', 'bookmark_id': str(bookmark.id)}


async def list_bookmarked_courses(db: AsyncSession, user_id: UUID) -> list[dict]:
    result = await db.execute(
        select(Bookmark, Course)
        .join(Course, Bookmark.course_id == Course.id)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
    )
    rows = result.all()
    return [
        {
            'bookmark_id': str(b.id),
            'course_id': str(c.id),
            'course_name': c.name,
            'college_name': '',
            'material_count': 0,
            'created_at': b.created_at,
        }
        for b, c in rows
    ]


async def list_bookmarked_materials(db: AsyncSession, user_id: UUID) -> list[dict]:
    result = await db.execute(
        select(Bookmark, Material, Course)
        .join(Material, Bookmark.material_id == Material.id)
        .join(Course, Material.course_id == Course.id)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
    )
    rows = result.all()
    return [
        {
            'bookmark_id': str(b.id),
            'material_id': str(m.id),
            'title': m.title,
            'course_name': c.name,
            'category': m.category,
            'semester': m.semester,
            'format': m.format,
            'file_size': m.file_size,
            'average_rating': float(m.average_rating or 0),
            'created_at': b.created_at,
        }
        for b, m, c in rows
    ]


async def get_notifications(
    db: AsyncSession, user_id: UUID, limit: int = 20, offset: int = 0
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_unread_notification_count(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
    )
    return result.scalar() or 0


async def mark_notification_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> bool:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        return False
    notification.is_read = True
    await db.flush()
    return True


async def mark_all_notifications_read(db: AsyncSession, user_id: UUID) -> None:
    from sqlalchemy import update

    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type: str,
    title: str,
    body: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(notification)
    await db.flush()
    return notification


async def notify_course_followers(
    db: AsyncSession, course_id: UUID, material_title: str, material_id: UUID
) -> None:
    rows = await db.execute(select(Bookmark.user_id).where(Bookmark.course_id == course_id))
    follower_ids = [row[0] for row in rows.all()]
    for uid in follower_ids:
        await create_notification(
            db,
            user_id=uid,
            type='course_update',
            title=f'关注的课程有新资料',
            body=f'《{material_title}》已通过审核',
            resource_type='material',
            resource_id=str(material_id),
        )


async def deactivate_account(
    db: AsyncSession, user_id: UUID, ip_address: str | None = None, user_agent: str | None = None
) -> bool:
    from sqlalchemy import update as sql_update

    user = await get_user(db, user_id)
    if user is None:
        return False
    user.is_active = False
    user.university_id = None
    user.university_id_lookup = None
    user.university_verified_at = None
    user.wechat_openid = None
    user.wechat_openid_lookup = None
    user.email = None
    user.email_lookup = None
    await db.flush()

    await db.execute(
        sql_update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .values(revoked=True)
    )
    await db.flush()

    from app.services.audit_service import log_action

    await log_action(
        db,
        user_id,
        'account_deactivated',
        resource=f'user:{user_id}',
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return True
