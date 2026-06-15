from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import SmsSendRequest, SmsVerifyRequest
from app.schemas.user import TokenResponse
from app.services.auth_service import SmsSendError, SmsVerifyError, send_sms_code, verify_sms_code

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/sms/send')
async def sms_send(body: SmsSendRequest, request: Request):
    ip = request.client.host if request.client else 'unknown'
    try:
        await send_sms_code(body.phone, ip)
    except SmsSendError as e:
        return {'code': 42900, 'data': None, 'message': str(e)}
    return {'code': 0, 'data': None, 'message': 'verification code sent'}


@router.post('/sms/verify')
async def sms_verify(body: SmsVerifyRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else 'unknown'
    try:
        tokens = await verify_sms_code(db, body.phone, body.code, ip)
    except SmsVerifyError as e:
        return {'code': 40000, 'data': None, 'message': str(e)}
    await db.commit()
    return {'code': 0, 'data': TokenResponse(**tokens).model_dump(), 'message': 'ok'}
