from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_deletion import GRACE_PERIOD_DAYS, AccountDeletion
from app.models.user import User


async def request_deletion(db: AsyncSession, user_id: UUID) -> AccountDeletion | None:
    existing = await db.scalar(select(AccountDeletion).where(AccountDeletion.user_id == user_id))
    if existing:
        if existing.status == 'pending':
            existing.cancelled_at = datetime.now(timezone.utc)
            existing.status = 'cancelled'
            return None
        if existing.status == 'cancelled':
            await db.delete(existing)

    deletion = AccountDeletion(
        user_id=user_id,
        status='pending',
        requested_at=datetime.now(timezone.utc),
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=GRACE_PERIOD_DAYS),
    )
    db.add(deletion)

    # Mark user as inactive immediately
    user = await db.get(User, user_id)
    if user:
        user.is_active = False

    await db.flush()
    return deletion


async def cancel_deletion(db: AsyncSession, user_id: UUID) -> bool:
    existing = await db.scalar(
        select(AccountDeletion).where(
            AccountDeletion.user_id == user_id,
            AccountDeletion.status == 'pending',
        )
    )
    if existing is None:
        return False

    existing.status = 'cancelled'
    existing.cancelled_at = datetime.now(timezone.utc)

    user = await db.get(User, user_id)
    if user:
        user.is_active = True

    await db.flush()
    return True


async def get_deletion_status(db: AsyncSession, user_id: UUID) -> AccountDeletion | None:
    return await db.scalar(select(AccountDeletion).where(AccountDeletion.user_id == user_id))


async def process_expired_deletions(db: AsyncSession) -> int:
    """Delete user data for expired deletion requests. Returns count of processed users."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AccountDeletion)
        .where(
            AccountDeletion.status == 'pending',
            AccountDeletion.scheduled_at <= now,
        )
        .limit(100)
    )
    expired = list(result.scalars().all())

    for deletion in expired:
        user = await db.get(User, deletion.user_id)
        if user:
            user.nickname = f'deleted_user_{str(user.id)[:8]}'
            user.email = None
            user.email_lookup = None
            user.avatar_url = None
            user.university_id = None
            user.university_id_lookup = None
            user.university_verified_at = None
            user.wechat_openid = None
            user.wechat_openid_lookup = None
            user.is_active = False
        deletion.status = 'completed'

    await db.flush()
    return len(expired)
