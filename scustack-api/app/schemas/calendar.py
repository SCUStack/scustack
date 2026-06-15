from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CalendarCreate(BaseModel):
    year: int
    semester: str = Field(max_length=20)
    event_name: str = Field(max_length=200)
    event_tag: str = Field(pattern='^(midterm|final|course_selection|vacation|other)$')
    start_date: date
    end_date: date


class CalendarUpdate(BaseModel):
    year: int | None = None
    semester: str | None = Field(None, max_length=20)
    event_name: str | None = Field(None, max_length=200)
    event_tag: str | None = Field(None, pattern='^(midterm|final|course_selection|vacation|other)$')
    start_date: date | None = None
    end_date: date | None = None


class CalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    year: int
    semester: str
    event_name: str
    event_tag: str
    start_date: date
    end_date: date
    created_at: datetime
