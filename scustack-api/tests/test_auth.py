import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


class TestSmsSend:
    async def test_send_ok(self, client):
        with patch('app.api.v1.auth.send_sms_code', new_callable=AsyncMock):
            resp = await client.post('/api/v1/auth/sms/send', json={'phone': '13800138000'})
            assert resp.status_code == 200
            assert resp.json()['code'] == 0

    async def test_send_invalid_phone(self, client):
        resp = await client.post('/api/v1/auth/sms/send', json={'phone': '12345'})
        assert resp.status_code == 422

    async def test_send_rate_limited_error(self, client):
        from app.services.auth_service import SmsSendError

        async def _raise(*args, **kwargs):
            raise SmsSendError('too frequent')

        with patch('app.api.v1.auth.send_sms_code', side_effect=_raise):
            resp = await client.post('/api/v1/auth/sms/send', json={'phone': '13800138000'})
            assert resp.json()['code'] == 42900


class TestSmsVerify:
    async def test_verify_ok(self, client):
        tokens = {'access_token': 'at', 'refresh_token': 'rt', 'token_type': 'bearer'}
        with patch('app.api.v1.auth.verify_sms_code', new_callable=AsyncMock, return_value=tokens):
            resp = await client.post('/api/v1/auth/sms/verify',
                                     json={'phone': '13800138000', 'code': '000000'})
            assert resp.status_code == 200
            body = resp.json()
            assert body['code'] == 0
            assert body['data']['access_token'] == 'at'

    async def test_verify_wrong_code(self, client):
        from app.services.auth_service import SmsVerifyError

        async def _raise(*args, **kwargs):
            raise SmsVerifyError('incorrect verification code')

        with patch('app.api.v1.auth.verify_sms_code', side_effect=_raise):
            resp = await client.post('/api/v1/auth/sms/verify',
                                     json={'phone': '13800138000', 'code': '999999'})
            assert resp.json()['code'] == 40000

    async def test_verify_expired_code(self, client):
        from app.services.auth_service import SmsVerifyError

        async def _raise(*args, **kwargs):
            raise SmsVerifyError('verification code expired or not sent')

        with patch('app.api.v1.auth.verify_sms_code', side_effect=_raise):
            resp = await client.post('/api/v1/auth/sms/verify',
                                     json={'phone': '13800138000', 'code': '123456'})
            assert resp.json()['code'] == 40000

    async def test_verify_invalid_request(self, client):
        resp = await client.post('/api/v1/auth/sms/verify',
                                 json={'phone': '13800138000', 'code': 'abc'})
        assert resp.status_code == 422


class TestJwtTokens:
    def test_create_and_decode_access_token(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token('test-user-id', 'student')
        payload = decode_token(token)
        assert payload['sub'] == 'test-user-id'
        assert payload['role'] == 'student'

    def test_refresh_token_is_unique(self):
        from app.core.security import create_refresh_token
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2
        assert len(t1) == 64
