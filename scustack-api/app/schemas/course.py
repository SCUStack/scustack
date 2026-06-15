from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    college_id: UUID
    name: str
    slug: str
    aliases: list[str] = []
    description: str | None = None
    credit: float | None = None
    category: str | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    credit: float | None = None
    category: str | None = None
    is_active: bool | None = None


class CollegeSimple(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    college_id: UUID
    college: CollegeSimple | None = None
    name: str
    slug: str
    aliases: list
    description: str | None
    credit: float | None
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
