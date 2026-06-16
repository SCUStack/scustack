import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RateLimitLog(Base):
    __tablename__ = 'rate_limit_logs'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    ip_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    limit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
