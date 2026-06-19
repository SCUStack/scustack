from app.core.database import async_session
from app.models.user import User
from app.services import audit_service


async def log_anti_scraping_event(
    action: str,
    route_id: str,
    detail: dict | None = None,
    *,
    current_user: User | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        async with async_session() as db:
            await audit_service.log_action(
                db,
                current_user.id if current_user is not None else None,
                f'anti_scraping.{action}',
                resource=f'anti_scraping:{route_id}',
                detail=detail,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await db.commit()
    except Exception:
        # Observability must never break the protected path itself.
        pass
