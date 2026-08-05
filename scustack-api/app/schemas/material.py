from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaterialCreate(BaseModel):
    title: str = Field(max_length=500)
    course_id: UUID
    category: str
    semester: str
    teacher: str | None = None
    source_type: str = 'hosted'
    external_url: str | None = None
    description: str | None = None
    storage_key: str | None = None
    file_hash: str | None = None
    file_size: int | None = None
    format: str | None = None
    parts: list[dict] | None = None
    upload_id: str | None = Field(None, min_length=32, max_length=64)


class MaterialUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    category: str | None = None
    semester: str | None = None
    teacher: str | None = None
    description: str | None = None
    parts: list[dict] | None = None


class ContributorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    avatar_url: str | None = None
    trust_score: int = 0
    badges: list[dict] = []


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    description: str | None
    category: str
    semester: str
    teacher: str | None
    source_type: str
    external_url: str | None
    format: str | None
    file_size: int | None
    file_hash: str | None
    trust_status: str
    review_status: str
    average_rating: float
    rating_count: int
    download_count: int
    rating_distribution: dict[str, int] | None = None
    is_pinned: bool
    link_checked_at: datetime | None = None
    link_status: str | None = None
    link_failure_count: int | None = 0
    virus_scan_status: str | None = None
    parts: list[dict] | None = None
    contributor_id: UUID | None
    contributor: ContributorInfo | None = None
    thumbnail_url: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator('link_failure_count', mode='before')
    @classmethod
    def default_link_failure_count(cls, value: int | None) -> int:
        return 0 if value is None else value


class UploadTokenRequest(BaseModel):
    file_name: str
    content_type: str
    file_size: int


class UploadTokenResponse(BaseModel):
    upload_url: str
    storage_key: str


class DuplicateCheckRequest(BaseModel):
    file_hash: str = Field(min_length=64, max_length=64)


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_material_id: UUID | None = None
    existing_title: str | None = None


class RatingRequest(BaseModel):
    score: int = Field(ge=1, le=5)


class VersionCreate(BaseModel):
    upload_id: str = Field(min_length=32, max_length=64)
    change_note: str | None = None


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID
    version_number: int
    file_hash: str
    file_size: int
    change_note: str | None
    uploaded_by: UUID | None
    created_at: datetime


class MaterialDetailResponse(BaseModel):
    material: MaterialResponse
    versions_preview: list[VersionResponse]
    related: list[MaterialResponse]
    course_name: str
    first_screen_request_count: int = 1
