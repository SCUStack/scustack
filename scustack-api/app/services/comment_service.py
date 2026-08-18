from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.user import User


async def create_comment(db: AsyncSession, material_id: UUID, user_id: UUID, content: str, parent_id: UUID | None = None) -> Comment:
    if parent_id:
        parent = await db.get(Comment, parent_id)
        if parent is None or str(parent.material_id) != str(material_id):
            raise ValueError('parent comment not found')
    comment = Comment(material_id=material_id, user_id=user_id, content=content, parent_id=parent_id)
    db.add(comment)
    await db.flush()
    return comment


async def list_comments(db: AsyncSession, material_id: UUID, limit: int = 50, offset: int = 0) -> list[dict]:
    # Get top-level comments with user info
    stmt = (
        select(Comment, User.nickname, User.avatar_url)
        .join(User, Comment.user_id == User.id)
        .where(Comment.material_id == material_id, Comment.parent_id.is_(None), Comment.is_deleted == False)
        .order_by(Comment.created_at.desc())
        .offset(offset).limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    comment_ids = [r[0].id for r in rows]
    reply_map: dict[UUID, list[dict]] = {}
    if comment_ids:
        reply_stmt = (
            select(Comment, User.nickname, User.avatar_url)
            .join(User, Comment.user_id == User.id)
            .where(Comment.parent_id.in_(comment_ids), Comment.is_deleted == False)
            .order_by(Comment.created_at.asc())
        )
        reply_result = await db.execute(reply_stmt)
        for c, nick, avatar_url in reply_result.all():
            reply_map.setdefault(c.parent_id, []).append(_format_comment(c, nick, avatar_url))

    return [_format_comment(c, nick, avatar_url, reply_map.get(c.id, [])) for c, nick, avatar_url in rows]


async def count_comments(db: AsyncSession, material_id: UUID) -> int:
    return await db.scalar(
        select(func.count(Comment.id)).where(
            Comment.material_id == material_id, Comment.is_deleted == False
        )
    ) or 0


async def delete_comment(db: AsyncSession, comment_id: UUID, user_id: UUID, role: str) -> bool:
    comment = await db.get(Comment, comment_id)
    if comment is None:
        return False
    if str(comment.user_id) != str(user_id) and role not in ('maintainer', 'admin'):
        return False
    comment.is_deleted = True
    comment.content = '[deleted]'
    await db.flush()
    return True


def _format_comment(c: Comment, nickname: str, avatar_url: str | None = None, replies: list[dict] | None = None) -> dict:
    return {
        'id': str(c.id),
        'material_id': str(c.material_id),
        'user_id': str(c.user_id),
        'nickname': nickname,
        'avatar_url': avatar_url,
        'content': c.content,
        'parent_id': str(c.parent_id) if c.parent_id else None,
        'is_deleted': c.is_deleted,
        'created_at': c.created_at.isoformat(),
        'replies': replies or [],
    }
