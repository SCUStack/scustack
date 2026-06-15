from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookmarkToggle(BaseModel):
    course_id: UUID | None = None
    material_id: UUID | None = None


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID | None = None
    material_id: UUID | None = None
    created_at: datetime


class BookmarkedCourse(BaseModel):
    bookmark_id: UUID
    course_id: UUID
    course_name: str
    college_name: str
    material_count: int
    created_at: datetime


class BookmarkedMaterial(BaseModel):
    bookmark_id: UUID
    material_id: UUID
    title: str
    course_name: str
    category: str
    semester: str
    format: str | None
    file_size: int | None
    average_rating: float
    created_at: datetime
