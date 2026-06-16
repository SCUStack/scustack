from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_consent import UserConsent

REQUIRED_CONSENTS = ('privacy_policy', 'terms_of_service', 'age_confirmation')


async def record_consents(db: AsyncSession, user_id: UUID, consents: dict[str, bool]) -> None:
    for ctype in REQUIRED_CONSENTS:
        if not consents.get(ctype):
            raise ValueError(f'consent required: {ctype}')
        existing = await db.scalar(
            select(UserConsent).where(UserConsent.user_id == user_id, UserConsent.consent_type == ctype)
        )
        if existing:
            existing.version = 'v1'
            existing.consented_at = db.func.now()
        else:
            db.add(UserConsent(user_id=user_id, consent_type=ctype))


async def check_missing_consents(db: AsyncSession, user_id: UUID) -> list[str]:
    result = await db.execute(
        select(UserConsent.consent_type).where(UserConsent.user_id == user_id)
    )
    given = {r[0] for r in result.all()}
    return [c for c in REQUIRED_CONSENTS if c not in given]
