import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.config import settings
from app.core.university_auth import (
    DisabledUniversityIdentityVerifier,
    MockUniversityIdentityVerifier,
    ScuCliUniversityIdentityVerifier,
    UniversityAuthUnavailableError,
    UniversityCredentialsRejectedError,
    get_university_identity_verifier,
)
from app.models.user import User
from app.services.auth_service import (
    PasswordError,
    login_with_university_id,
    register_with_university,
)
from app.services.user_service import get_masked_university_id

TOKENS = {'access_token': 'access', 'refresh_token': 'refresh', 'token_type': 'bearer'}


def _db_with_user(user: User | None):
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    return db


class TestUniversityRegistrationService:
    async def test_verifies_identity_and_stores_only_local_credentials(self):
        db = _db_with_user(None)
        verifier = MagicMock()
        verifier.verify = AsyncMock()

        with (
            patch('app.services.auth_service._issue_tokens', AsyncMock(return_value=TOKENS)),
            patch('app.services.auth_service._audit_auth', AsyncMock()),
        ):
            tokens = await register_with_university(
                db,
                '2026123456789',
                'school-secret',
                'local-pass-1',
                verifier,
            )

        assert tokens == TOKENS
        verifier.verify.assert_awaited_once_with('2026123456789', 'school-secret')
        created_user = db.add.call_args.args[0]
        assert created_user.university_id != '2026123456789'
        assert created_user.university_id_lookup
        assert created_user.university_verified_at is not None
        assert created_user.password_hash != 'local-pass-1'
        assert 'school-secret' not in vars(created_user).values()

    async def test_duplicate_student_id_skips_external_verification(self):
        db = _db_with_user(User(nickname='existing'))
        verifier = MagicMock()
        verifier.verify = AsyncMock()

        with patch('app.services.auth_service._audit_auth', AsyncMock()):
            with pytest.raises(PasswordError, match='已注册'):
                await register_with_university(
                    db,
                    '2026123456789',
                    'school-secret',
                    'local-pass-1',
                    verifier,
                )

        verifier.verify.assert_not_awaited()


class TestUniversityLoginService:
    async def test_logs_in_by_student_id_lookup(self):
        user = User(
            nickname='student',
            role='student',
            trust_score=0,
            is_active=True,
            password_hash='hashed-local-password',
        )
        user.id = uuid4()
        db = _db_with_user(user)

        with (
            patch('app.services.auth_service.cache_get', AsyncMock(return_value=None)),
            patch('app.services.auth_service.cache_delete', AsyncMock()),
            patch('app.services.auth_service._verify_password', return_value=True),
            patch('app.services.auth_service._issue_tokens', AsyncMock(return_value=TOKENS)),
            patch('app.services.auth_service._audit_auth', AsyncMock()),
        ):
            tokens = await login_with_university_id(db, '2026123456789', 'local-pass-1')

        assert tokens == TOKENS
        assert 'university_id_lookup' in str(db.execute.await_args.args[0])


class TestUniversityVerifierConfiguration:
    async def test_disabled_provider_fails_closed(self):
        verifier = DisabledUniversityIdentityVerifier()
        with pytest.raises(UniversityAuthUnavailableError):
            await verifier.verify('2026123456789', 'secret')

    async def test_mock_provider_requires_configured_password(self):
        verifier = MockUniversityIdentityVerifier('expected')
        with pytest.raises(UniversityCredentialsRejectedError):
            await verifier.verify('2026123456789', 'wrong')

    def test_factory_uses_disabled_provider_by_default(self):
        with patch.object(settings, 'UNIVERSITY_AUTH_PROVIDER', 'disabled'):
            assert isinstance(
                get_university_identity_verifier(), DisabledUniversityIdentityVerifier
            )

    def test_scu_cli_parser_reads_json_after_prompts(self):
        result = ScuCliUniversityIdentityVerifier._parse_result(
            '学号: 2026123456789\r\n密码: \r\n'
            '{\r\n  "ok": true,\r\n  "data": {"principal": "2026123456789"}\r\n}\r\n'
        )
        assert result['ok'] is True

    @pytest.mark.skipif(os.name == 'nt', reason='POSIX pseudo-terminal required')
    async def test_scu_cli_uses_tty_and_removes_temporary_credentials(self, tmp_path):
        fake_cli = tmp_path / 'fake-scu'
        fake_cli.write_text(
            '#!/bin/sh\n'
            'test "$#" -eq 1 || exit 2\n'
            'printf "学号: " >&2\n'
            'read university_id\n'
            'printf "密码: " >&2\n'
            'stty -echo\n'
            'read password\n'
            'stty echo\n'
            'printf "\\n" >&2\n'
            'printf "%s" "$password" > "$SCU_CLI_CONFIG_DIR/credentials.json"\n'
            'printf \'{"ok":true,"data":{"principal":"%s"}}\\n\' "$university_id"\n',
            encoding='utf-8',
        )
        fake_cli.chmod(0o700)
        runtime_dir = tmp_path / 'runtime'
        runtime_dir.mkdir()

        verifier = ScuCliUniversityIdentityVerifier(str(fake_cli), 5, str(runtime_dir))
        await verifier.verify('2026123456789', 'school-secret')

        assert list(runtime_dir.iterdir()) == []


def test_student_id_is_masked_before_returning_to_frontend():
    user = User(nickname='student', university_id='encrypted')
    with patch('app.core.security.decrypt_pii', return_value='2026123456789'):
        assert get_masked_university_id(user) == '2026****6789'
