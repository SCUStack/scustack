from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewAction(BaseModel):
    action: str = Field(pattern='^(approved|rejected|returned)$')
    comment: str | None = None


class ReviewBatchAction(BaseModel):
    material_ids: list[UUID]
    action: str = Field(pattern='^(approved|rejected)$')
    comment: str | None = None


class ReviewQueueItem(BaseModel):
    material_id: UUID
    title: str
    course_name: str
    category: str
    semester: str
    contributor_id: UUID | None
    format: str | None
    file_size: int | None
    trust_status: str
    review_status: str
    submitted_at: datetime


class ReviewLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID
    reviewer_id: UUID
    action: str
    comment: str | None
    created_at: datetime
