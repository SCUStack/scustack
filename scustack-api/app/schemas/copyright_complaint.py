from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CopyrightComplaintCreate(BaseModel):
    complainant_name: str = Field(min_length=1, max_length=100)
    contact_email: str = Field(min_length=1, max_length=200)
    contact_phone: str | None = None
    infringing_url: str = Field(min_length=1, max_length=2000)
    infringing_description: str | None = None
    statement: str = Field(min_length=10, max_length=5000)


class CopyrightComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_number: str
    complainant_name: str
    contact_email: str
    contact_phone: str | None = None
    infringing_url: str
    infringing_description: str | None = None
    statement: str
    status: str
    resolution_note: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class ComplaintResolveRequest(BaseModel):
    status: str = Field(pattern='^(resolved|dismissed)$')
    resolution_note: str | None = None
