from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CollegeCreate(BaseModel):
    name: str
    slug: str
    sort_order: int = 0
    description: str | None = None
    website: str | None = None


class CollegeUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    description: str | None = None
    website: str | None = None


class CollegeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    sort_order: int
    description: str | None = None
    website: str | None = None
