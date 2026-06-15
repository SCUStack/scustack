from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CollegeCreate(BaseModel):
    name: str
    slug: str
    sort_order: int = 0


class CollegeUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None


class CollegeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    sort_order: int
