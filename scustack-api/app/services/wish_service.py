from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish import Wish, WishVote

MAX_OPEN_WISHES_PER_COURSE = 3


async def create_wish(
    db: AsyncSession,
    user_id: UUID,
    course_id: UUID,
    title: str,
    description: str | None = None,
    category: str | None = None,
) -> Wish:
    open_count = await db.scalar(
        select(func.count(Wish.id)).where(
            Wish.user_id == user_id,
            Wish.course_id == course_id,
            Wish.status == 'open',
        )
    )
    if open_count and open_count >= MAX_OPEN_WISHES_PER_COURSE:
        raise ValueError(f'每门课最多 {MAX_OPEN_WISHES_PER_COURSE} 条心愿')

    wish = Wish(
        user_id=user_id,
        course_id=course_id,
        title=title,
        description=description,
        category=category,
    )
    db.add(wish)
    await db.flush()

    vote = WishVote(wish_id=wish.id, user_id=user_id)
    db.add(vote)

    return wish


async def list_wishes(
    db: AsyncSession,
    course_id: UUID | None = None,
    status: str = 'open',
    sort: str = 'votes',
    limit: int = 20,
    offset: int = 0,
    current_user_id: UUID | None = None,
) -> list[dict]:
    stmt = select(Wish).where(Wish.status == status)
    if course_id:
        stmt = stmt.where(Wish.course_id == course_id)

    if sort == 'newest':
        stmt = stmt.order_by(Wish.created_at.desc())
    else:
        stmt = stmt.order_by(Wish.vote_count.desc(), Wish.created_at.desc())

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    wishes = list(result.scalars().all())

    output = []
    for w in wishes:
        has_voted = False
        if current_user_id:
            vote_result = await db.execute(
                select(WishVote).where(
                    WishVote.wish_id == w.id,
                    WishVote.user_id == current_user_id,
                )
            )
            has_voted = vote_result.scalar_one_or_none() is not None
        output.append({
            'id': w.id,
            'user_id': w.user_id,
            'course_id': w.course_id,
            'title': w.title,
            'description': w.description,
            'category': w.category,
            'status': w.status,
            'fulfill_material_id': w.fulfill_material_id,
            'vote_count': w.vote_count,
            'has_voted': has_voted,
            'created_at': w.created_at,
        })
    return output


async def count_wishes(
    db: AsyncSession,
    course_id: UUID | None = None,
    status: str = 'open',
) -> int:
    stmt = select(func.count(Wish.id)).where(Wish.status == status)
    if course_id:
        stmt = stmt.where(Wish.course_id == course_id)
    return await db.scalar(stmt) or 0


async def vote_wish(db: AsyncSession, wish_id: UUID, user_id: UUID) -> dict:
    wish = await db.get(Wish, wish_id)
    if wish is None:
        raise ValueError('wish not found')

    existing = await db.execute(
        select(WishVote).where(
            WishVote.wish_id == wish_id,
            WishVote.user_id == user_id,
        )
    )
    vote = existing.scalar_one_or_none()

    if vote:
        await db.delete(vote)
        wish.vote_count = max(0, wish.vote_count - 1)
        action = 'unvoted'
    else:
        db.add(WishVote(wish_id=wish_id, user_id=user_id))
        wish.vote_count = wish.vote_count + 1
        action = 'voted'

    await db.flush()
    return {'action': action, 'vote_count': wish.vote_count}


async def fulfill_wish(db: AsyncSession, wish_id: UUID, material_id: UUID, user_id: UUID) -> Wish:
    wish = await db.get(Wish, wish_id)
    if wish is None:
        raise ValueError('wish not found')
    if str(wish.user_id) != str(user_id):
        raise ValueError('only the wish creator can mark it as fulfilled')

    wish.status = 'fulfilled'
    wish.fulfill_material_id = material_id
    await db.flush()
    return wish
