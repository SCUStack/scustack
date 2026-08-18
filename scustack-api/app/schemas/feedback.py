from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    type: str = Field(max_length=20)
    content: str = Field(max_length=2000)
    email: str | None = Field(None, max_length=200)

class FeedbackHandle(BaseModel):
    status: str = Field(pattern='^(resolved|ignored|pending)$')
    admin_note: str | None = Field(None, max_length=2000)

class FeedbackResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    type: str
    content: str
    email: str | None
    status: str
    handled_by: UUID | None
    handled_at: datetime | None
    admin_note: str | None
    created_at: datetime
    model_config = {'from_attributes': True}
