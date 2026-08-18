from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    avatar_url: str | None
    role: str
    trust_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=64)
    avatar_url: str | None = Field(None, max_length=512)
    public_display_name: str | None = Field(None, max_length=64)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    avatar_url: str | None
    role: str
    trust_score: int
    public_display_name: str | None
    university_id_masked: str | None = None
    created_at: datetime


class ContributionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    course_id: UUID
    category: str
    semester: str
    review_status: str
    trust_status: str
    download_count: int
    average_rating: float
    created_at: datetime


class PrivacySettings(BaseModel):
    public_display_name: str = '匿名用户'


class DeactivateRequest(BaseModel):
    confirm: bool = Field(False, description='Must be true to confirm deactivation')


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
