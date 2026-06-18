import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.models.material import Material
from app.models.user import User, RefreshToken


class TestUserModel:
    def test_create_user(self):
        user = User(
            phone='encrypted_phone_hex',
            phone_lookup='lookup_hash',
            nickname='测试用户',
            role='student',
            trust_score=0,
            is_active=True,
        )
        assert user.nickname == '测试用户'
        assert user.role == 'student'
        assert user.trust_score == 0
        assert user.is_active is True
        assert user.wechat_openid is None
        assert user.university_id is None
        assert user.avatar_url is None

    def test_user_defaults(self):
        user = User(
            phone='encrypted_phone_hex',
            phone_lookup='lookup_hash',
            nickname='test',
            role='student',
            trust_score=0,
            is_active=True,
        )
        assert user.trust_score == 0
        assert user.is_active is True
        assert user.role == 'student'

    def test_refresh_token_model(self):
        user_id = uuid.uuid4()
        token = RefreshToken(
            user_id=user_id,
            token_hash='abc123',
            expires_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
            revoked=False,
        )
        assert token.user_id == user_id
        assert token.token_hash == 'abc123'
        assert token.revoked is False
        assert token.expires_at.year == 2026


class TestMaterialModel:
    def test_thumbnail_url_returns_none_when_thumbnail_missing(self):
        material = Material(
            course_id=uuid.uuid4(),
            title='Test',
            category='notes',
            semester='2025-2026-1',
            source_type='hosted',
        )
        material.id = uuid.uuid4()

        with patch('app.core.oss.thumbnail_exists', return_value=False):
            assert material.thumbnail_url is None
