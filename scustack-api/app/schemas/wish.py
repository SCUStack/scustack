from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WishCreate(BaseModel):
    course_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None


class WishResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    course_id: UUID
    title: str
    description: str | None = None
    category: str | None = None
    status: str
    fulfill_material_id: UUID | None = None
    vote_count: int
    has_voted: bool = False
    created_at: datetime


class WishFulfillRequest(BaseModel):
    material_id: UUID
