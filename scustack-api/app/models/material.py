import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Material(Base):
    __tablename__ = 'materials'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    teacher: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trust_status: Mapped[str] = mapped_column(
        String(20), nullable=False, insert_default='unverified', server_default='unverified'
    )
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, insert_default='pending', server_default='pending'
    )
    average_rating: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, insert_default=0, server_default='0'
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, nullable=False, insert_default=0, server_default='0'
    )
    download_count: Mapped[int] = mapped_column(
        Integer, nullable=False, insert_default=0, server_default='0'
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, insert_default=False, server_default='false'
    )
    link_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    link_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    link_failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, insert_default=0, server_default='0'
    )
    virus_scan_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    parts: Mapped[list | None] = mapped_column(
        JSONB, nullable=True
    )
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    versions: Mapped[list['MaterialVersion']] = relationship(
        'MaterialVersion', back_populates='material', cascade='all, delete-orphan'
    )

    # Non-mapped — populated at query time by get_material
    rating_distribution: ClassVar[dict | None] = None

    @property
    def thumbnail_url(self) -> str | None:
        try:
            from app.core.thumbnails import thumbnail_url
            return thumbnail_url(self.id)
        except Exception:
            return None


class MaterialVersion(Base):
    __tablename__ = 'material_versions'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('materials.id', ondelete='CASCADE'), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    material: Mapped[Material] = relationship('Material', back_populates='versions')


class MaterialFileReplica(Base):
    __tablename__ = 'material_file_replicas'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    material_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('material_versions.id', ondelete='CASCADE'), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_instance: Mapped[str] = mapped_column(String(100), nullable=False)
    locator: Mapped[str] = mapped_column(String(2000), nullable=False)
    access_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default='pending')
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
