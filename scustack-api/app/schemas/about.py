from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class HeatmapDay(BaseModel):
    date: date
    count: int


class ContributorInfo(BaseModel):
    user_id: UUID
    display_name: str
    is_anonymous: bool
    material_count: int
    total_downloads: int


class AboutStats(BaseModel):
    college_count: int
    course_count: int
    material_count: int
    contributor_count: int
    total_downloads: int
    founded_at: datetime | None = None
