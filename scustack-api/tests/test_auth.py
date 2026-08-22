from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c


def _mock_rate_limiter():
    """Patch RateLimiter so auth tests don't fail on missing Redis."""
    mock_limiter = MagicMock()
    mock_limiter.is_allowed = AsyncMock(return_value=True)
    mock_limiter.limit_headers = AsyncMock(return_value={})
    return patch('app.api.v1.auth.RateLimiter', return_value=mock_limiter)


TOKENS = {'access_token': 'at', 'refresh_token': 'rt', 'token_type': 'bearer'}


class TestUniversityAuthentication:
    async def test_register_sets_cookies(self, client):
        with (
            _mock_rate_limiter(),
            patch(
                'app.api.v1.auth.register_with_university',
                new_callable=AsyncMock,
                return_value=TOKENS,
            ),
        ):
            resp = await client.post(
                '/api/v1/auth/register',
                json={
                    'university_id': '2026123456789',
                    'university_password': 'school-secret',
                    'password': 'local-pass-1',
                    'confirm_password': 'local-pass-1',
                },
            )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0
        assert 'access_token' in resp.cookies
        assert 'refresh_token' in resp.cookies
        assert 'csrf_token' in resp.cookies

    async def test_register_rejects_invalid_school_credentials(self, client):
        from app.core.university_auth import UniversityCredentialsRejectedError

        with (
            _mock_rate_limiter(),
            patch(
                'app.api.v1.auth.register_with_university',
                new_callable=AsyncMock,
                side_effect=UniversityCredentialsRejectedError,
            ),
        ):
            resp = await client.post(
                '/api/v1/auth/register',
                json={
                    'university_id': '2026123456789',
                    'university_password': 'wrong',
                    'password': 'local-pass-1',
                    'confirm_password': 'local-pass-1',
                },
            )
        assert resp.status_code == 401
        assert resp.json()['message'] == '川大账号或密码不正确'

    async def test_register_reports_unavailable_identity_service(self, client):
        from app.core.university_auth import UniversityAuthUnavailableError

        with (
            _mock_rate_limiter(),
            patch(
                'app.api.v1.auth.register_with_university',
                new_callable=AsyncMock,
                side_effect=UniversityAuthUnavailableError,
            ),
        ):
            resp = await client.post(
                '/api/v1/auth/register',
                json={
                    'university_id': '2026123456789',
                    'university_password': 'school-secret',
                    'password': 'local-pass-1',
                    'confirm_password': 'local-pass-1',
                },
            )

        assert resp.status_code == 503
        assert resp.json() == {
            'code': 50300,
            'data': None,
            'message': '川大身份校验服务暂不可用',
        }

    async def test_register_validates_student_id_and_local_password(self, client):
        resp = await client.post(
            '/api/v1/auth/register',
            json={
                'university_id': 'not-a-student-id',
                'university_password': 'school-secret',
                'password': 'password-only',
                'confirm_password': 'password-only',
            },
        )
        assert resp.status_code == 422

    async def test_login_uses_university_id(self, client):
        login = AsyncMock(return_value=TOKENS)
        with _mock_rate_limiter(), patch('app.api.v1.auth.login_with_university_id', login):
            resp = await client.post(
                '/api/v1/auth/login',
                json={'university_id': '2026123456789', 'password': 'local-pass-1'},
            )
        assert resp.status_code == 200
        assert login.await_args.args[1:3] == ('2026123456789', 'local-pass-1')

    async def test_phone_login_is_removed(self, client):
        resp = await client.post(
            '/api/v1/auth/login',
            json={'phone': '13800138000', 'password': 'local-pass-1'},
        )
        assert resp.status_code == 422

    async def test_sms_routes_are_removed(self, client):
        resp = await client.post('/api/v1/auth/sms/send', json={'phone': '13800138000'})
        assert resp.status_code == 404


class TestRefresh:
    async def test_refresh_ok_rotates(self, client):
        new_tokens = {'access_token': 'at2', 'refresh_token': 'rt2', 'token_type': 'bearer'}
        with (
            _mock_rate_limiter(),
            patch(
                'app.api.v1.auth.refresh_tokens', new_callable=AsyncMock, return_value=new_tokens
            ),
        ):
            client.cookies.set('refresh_token', 'rt-old')
            client.cookies.set('csrf_token', 'csrf-test')
            resp = await client.post('/api/v1/auth/refresh', headers={'X-CSRF-Token': 'csrf-test'})
            assert resp.status_code == 200
            assert resp.json()['data'] is None

    async def test_refresh_no_cookie(self, client):
        with _mock_rate_limiter():
            resp = await client.post('/api/v1/auth/refresh')
            assert resp.status_code == 401

    async def test_refresh_reuse_detected(self, client):
        from app.services.auth_service import AuthError

        async def _raise(*args, **kwargs):
            raise AuthError('token reuse detected, all sessions revoked')

        with _mock_rate_limiter(), patch('app.api.v1.auth.refresh_tokens', side_effect=_raise):
            client.cookies.set('refresh_token', 'rt-reused')
            client.cookies.set('csrf_token', 'csrf-test')
            resp = await client.post('/api/v1/auth/refresh', headers={'X-CSRF-Token': 'csrf-test'})
            assert resp.status_code == 401
            assert 'token reuse' in resp.json()['message']


class TestLogout:
    async def test_logout_clears_cookies(self, client):
        with patch('app.api.v1.auth.revoke_refresh_token', new_callable=AsyncMock):
            client.cookies.set('refresh_token', 'rt-to-revoke')
            client.cookies.set('csrf_token', 'csrf-test')
            resp = await client.post('/api/v1/auth/logout', headers={'X-CSRF-Token': 'csrf-test'})
            assert resp.json()['code'] == 0

    async def test_logout_no_cookie(self, client):
        resp = await client.post('/api/v1/auth/logout')
        assert resp.json()['code'] == 0


class TestCsrfToken:
    async def test_csrf_endpoint_sets_cookie(self, client):
        resp = await client.get('/api/v1/auth/csrf')
        assert resp.status_code == 200
        assert resp.json()['code'] == 0
        assert 'csrf_token' in resp.cookies

    async def test_csrf_cookie_supports_shared_parent_domain(self, client):
        with patch('app.api.v1.auth.CSRF_COOKIE_DOMAIN', '.scustack.cn'):
            resp = await client.get('/api/v1/auth/csrf')

        assert 'Domain=.scustack.cn' in resp.headers['set-cookie']
        assert 'Max-Age=0' in resp.headers['set-cookie']


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
        from jose.exceptions import ExpiredSignatureError

        from app.core.config import settings
        from app.core.security import create_access_token, decode_token

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
        from app.core.permissions import ROLE_PERMISSIONS, Permission

        assert Permission.MATERIALS_READ in ROLE_PERMISSIONS['visitor']
        assert Permission.MATERIALS_CREATE not in ROLE_PERMISSIONS['visitor']
        assert Permission.MATERIALS_MODERATE in ROLE_PERMISSIONS['maintainer']
        assert Permission.USERS_MANAGE not in ROLE_PERMISSIONS['maintainer']
        assert Permission.USERS_MANAGE in ROLE_PERMISSIONS['admin']
        assert Permission.USERS_MANAGE in ROLE_PERMISSIONS['admin']

    def test_admin_has_all_permissions(self):
        from app.core.permissions import ROLE_PERMISSIONS, Permission

        for perm in Permission:
            assert perm in ROLE_PERMISSIONS['admin']
