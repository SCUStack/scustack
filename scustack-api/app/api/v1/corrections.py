"""Correction suggestions API."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.correction import CorrectionSuggestion
from app.models.user import User
from pydantic import BaseModel, Field

router = APIRouter(prefix='/materials', tags=['corrections'])


class CorrectionCreate(BaseModel):
    field_name: str = Field(max_length=32)
    current_value: str = Field(max_length=1000)
    suggested_value: str = Field(max_length=1000)
    reason: str | None = Field(None, max_length=2000)


@router.post('/{material_id}/corrections')
async def suggest_correction(
    material_id: UUID,
    body: CorrectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Daily limit: 10
    from datetime import date
    today = date.today()
    count = await db.execute(
        select(func.count(CorrectionSuggestion.id)).where(
            CorrectionSuggestion.user_id == current_user.id,
            func.date(CorrectionSuggestion.created_at) == today,
        )
    )
    if (count.scalar() or 0) >= 10:
        return JSONResponse({'code': 42900, 'data': None, 'message': '今日建议已达上限'}, status_code=429)

    # Upsert: one pending per user per material per field
    result = await db.execute(
        select(CorrectionSuggestion).where(
            CorrectionSuggestion.material_id == material_id,
            CorrectionSuggestion.user_id == current_user.id,
            CorrectionSuggestion.field_name == body.field_name,
            CorrectionSuggestion.status == 'pending',
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.suggested_value = body.suggested_value
        existing.current_value = body.current_value
        existing.reason = body.reason
    else:
        cs = CorrectionSuggestion(
            material_id=material_id,
            user_id=current_user.id,
            field_name=body.field_name,
            current_value=body.current_value,
            suggested_value=body.suggested_value,
            reason=body.reason,
        )
        db.add(cs)

    await db.commit()
    return {'code': 0, 'data': None, 'message': '修正建议已提交'}
