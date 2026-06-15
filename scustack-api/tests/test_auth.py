import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


TOKENS = {'access_token': 'at', 'refresh_token': 'rt', 'token_type': 'bearer'}


class TestSmsSend:
    async def test_send_ok(self, client):
        with patch('app.api.v1.auth.send_sms_code', new_callable=AsyncMock):
            resp = await client.post('/api/v1/auth/sms/send', json={'phone': '13800138000'})
            assert resp.json()['code'] == 0

    async def test_send_invalid_phone(self, client):
        resp = await client.post('/api/v1/auth/sms/send', json={'phone': '12345'})
        assert resp.status_code == 422

    async def test_send_rate_limited(self, client):
        from app.services.auth_service import SmsSendError

        async def _raise(*args, **kwargs):
            raise SmsSendError('too frequent')

        with patch('app.api.v1.auth.send_sms_code', side_effect=_raise):
            resp = await client.post('/api/v1/auth/sms/send', json={'phone': '13800138000'})
            assert resp.json()['code'] == 42900


class TestSmsVerify:
    async def test_verify_ok_sets_cookies(self, client):
        with patch('app.api.v1.auth.verify_sms_code', new_callable=AsyncMock, return_value=TOKENS):
            resp = await client.post('/api/v1/auth/sms/verify',
                                     json={'phone': '13800138000', 'code': '000000'})
            assert resp.status_code == 200
            body = resp.json()
            assert body['code'] == 0
            assert body['data']['access_token'] == 'at'
            assert 'access_token' in resp.cookies
            assert 'refresh_token' in resp.cookies

    async def test_verify_wrong_code(self, client):
        from app.services.auth_service import SmsVerifyError

        async def _raise(*args, **kwargs):
            raise SmsVerifyError('incorrect')

        with patch('app.api.v1.auth.verify_sms_code', side_effect=_raise):
            resp = await client.post('/api/v1/auth/sms/verify',
                                     json={'phone': '13800138000', 'code': '999999'})
            assert resp.json()['code'] == 40000

    async def test_verify_invalid_request(self, client):
        resp = await client.post('/api/v1/auth/sms/verify',
                                 json={'phone': '13800138000', 'code': 'abc'})
        assert resp.status_code == 422


class TestRefresh:
    async def test_refresh_ok_rotates(self, client):
        new_tokens = {'access_token': 'at2', 'refresh_token': 'rt2', 'token_type': 'bearer'}
        with patch('app.api.v1.auth.refresh_tokens', new_callable=AsyncMock, return_value=new_tokens):
            client.cookies.set('refresh_token', 'rt-old')
            resp = await client.post('/api/v1/auth/refresh')
            assert resp.status_code == 200
            assert resp.json()['data']['access_token'] == 'at2'

    async def test_refresh_no_cookie(self, client):
        resp = await client.post('/api/v1/auth/refresh')
        assert resp.status_code == 401

    async def test_refresh_reuse_detected(self, client):
        from app.services.auth_service import AuthError

        async def _raise(*args, **kwargs):
            raise AuthError('token reuse detected, all sessions revoked')

        with patch('app.api.v1.auth.refresh_tokens', side_effect=_raise):
            client.cookies.set('refresh_token', 'rt-reused')
            resp = await client.post('/api/v1/auth/refresh')
            assert resp.status_code == 401
            assert 'token reuse' in resp.json()['message']


class TestLogout:
    async def test_logout_clears_cookies(self, client):
        with patch('app.api.v1.auth.revoke_refresh_token', new_callable=AsyncMock):
            client.cookies.set('refresh_token', 'rt-to-revoke')
            resp = await client.post('/api/v1/auth/logout')
            assert resp.json()['code'] == 0

    async def test_logout_no_cookie(self, client):
        resp = await client.post('/api/v1/auth/logout')
        assert resp.json()['code'] == 0


class TestJwtTokens:
    def test_create_and_decode(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token('user-1', 'student')
        payload = decode_token(token)
        assert payload['sub'] == 'user-1'
        assert payload['role'] == 'student'

    def test_refresh_token_unique(self):
        from app.core.security import create_refresh_token
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2
        assert len(t1) == 64

    def test_token_hash(self):
        from app.core.security import hash_token
        assert hash_token('abc') == hash_token('abc')
        assert hash_token('abc') != hash_token('def')
        assert len(hash_token('test')) == 64

    def test_expired_token_raises(self):
        from app.core.config import settings
        from app.core.security import create_access_token, decode_token
        from jose.exceptions import ExpiredSignatureError

        original = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = -1
        try:
            token = create_access_token('user-1', 'student')
            with pytest.raises(ExpiredSignatureError):
                decode_token(token)
        finally:
            settings.ACCESS_TOKEN_EXPIRE_MINUTES = original


class TestGetCurrentUser:
    async def test_no_cookie_returns_401(self, client):
        resp = await client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    async def test_invalid_token_returns_401(self, client):
        client.cookies.set('access_token', 'not-a-valid-jwt')
        resp = await client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    async def test_valid_auth_returns_user(self, client):
        from unittest.mock import MagicMock
        from app.dependencies import get_current_user as original_get_current_user

        mock_user = MagicMock()
        mock_user.id = '00000000-0000-0000-0000-000000000001'
        mock_user.nickname = 'testuser'
        mock_user.role = 'student'
        mock_user.avatar_url = None
        mock_user.trust_score = 0

        async def _override():
            return mock_user

        app.dependency_overrides[original_get_current_user] = _override
        try:
            resp = await client.get('/api/v1/auth/me')
            assert resp.status_code == 200
            body = resp.json()
            assert body['data']['nickname'] == 'testuser'
            assert body['data']['role'] == 'student'
        finally:
            app.dependency_overrides.clear()


class TestPermissions:
    def test_role_permission_mapping(self):
        from app.core.permissions import Permission, ROLE_PERMISSIONS
        assert Permission.MATERIALS_READ in ROLE_PERMISSIONS['visitor']
        assert Permission.MATERIALS_CREATE not in ROLE_PERMISSIONS['visitor']
        assert Permission.MATERIALS_MODERATE in ROLE_PERMISSIONS['maintainer']
        assert Permission.USERS_MANAGE not in ROLE_PERMISSIONS['maintainer']
        assert Permission.USERS_MANAGE in ROLE_PERMISSIONS['admin']

    def test_admin_has_all_permissions(self):
        from app.core.permissions import Permission, ROLE_PERMISSIONS
        for perm in Permission:
            assert perm in ROLE_PERMISSIONS['admin']

