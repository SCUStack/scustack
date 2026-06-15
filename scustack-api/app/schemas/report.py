from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    reason: str = Field(pattern='^(copyright|outdated|inappropriate|duplicate|wrong_info|other)$')
    description: str | None = None


class ReportHandle(BaseModel):
    action: str = Field(pattern='^(accepted|rejected)$')
    comment: str | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID
    reporter_id: UUID
    reason: str
    description: str | None
    status: str
    handled_by: UUID | None
    handled_at: datetime | None
    created_at: datetime


class ReportQueueItem(BaseModel):
    report_id: UUID
    material_id: UUID
    material_title: str
    reason: str
    description: str | None
    reporter_id: UUID
    status: str
    created_at: datetime
