from app.core.config import Settings


def _settings(**overrides):
    return Settings(_env_file=None, **overrides)


class TestSettings:
    def test_defaults(self):
        s = _settings()
        assert s.APP_NAME == 'scustack-api'
        assert s.APP_ENV == 'dev'
        assert s.DEBUG is False
        assert s.DB_POOL_SIZE == 20

    def test_database_url(self):
        s = _settings()
        url = s.DATABASE_URL
        assert url.startswith('postgresql+asyncpg://')
        assert 'scustack:scustack@localhost' in url and '/scustack' in url

    def test_is_dev(self):
        s = _settings()
        assert s.is_dev is True

    def test_session_cookie_secure_defaults_and_explicit_override(self):
        assert _settings(APP_ENV='dev').session_cookie_secure is False
        assert _settings(APP_ENV='prod').session_cookie_secure is True
        assert _settings(APP_ENV='prod', COOKIE_SECURE=False).session_cookie_secure is False

    def test_validate_secrets_reports_default_keys(self):
        s = _settings(
            JWT_SECRET_KEY='change-me-in-production',
            ENCRYPTION_KEY='change-me-in-production',
            DB_PASSWORD='scustack',
        )
        issues = s.validate_secrets()
        assert any('JWT_SECRET_KEY' in i for i in issues)
        assert any('ENCRYPTION_KEY' in i for i in issues)
        assert any('DB_PASSWORD' in i for i in issues)

    def test_validate_secrets_clean_when_keys_are_custom(self):
        s = _settings(
            JWT_SECRET_KEY='prod-jwt-secret-at-least-32-characters',
            ENCRYPTION_KEY='prod-encryption-key-at-least-32-chars',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
            TRUSTED_HOSTS=['api.example.com'],
        )
        issues = s.validate_secrets()
        assert len(issues) == 0

    def test_validate_secrets_includes_all_required_fields(self):
        s = _settings(
            JWT_SECRET_KEY='change-me-in-production',
            ENCRYPTION_KEY='change-me-in-production',
            DB_PASSWORD='scustack',
        )
        issues = s.validate_secrets()
        assert len(issues) == 4

    def test_validate_secrets_requires_default_lfs_token(self):
        s = _settings(
            JWT_SECRET_KEY='prod-jwt-secret-at-least-32-characters',
            ENCRYPTION_KEY='prod-encryption-key-at-least-32-chars',
            DB_PASSWORD='strong-db-password',
        )
        issues = s.validate_secrets()
        assert any('LFS_API_TOKEN' in issue for issue in issues)

    def test_validate_secrets_rejects_debug_in_production(self):
        s = _settings(
            APP_ENV='prod',
            DEBUG=True,
            JWT_SECRET_KEY='prod-jwt-secret-at-least-32-characters',
            ENCRYPTION_KEY='prod-encryption-key-at-least-32-chars',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
            TRUSTED_HOSTS=['api.example.com'],
        )
        assert 'DEBUG must be disabled in production' in s.validate_secrets()

    def test_validate_secrets_requires_trusted_hosts_in_production(self):
        s = _settings(
            APP_ENV='prod',
            JWT_SECRET_KEY='prod-jwt-secret-at-least-32-characters',
            ENCRYPTION_KEY='prod-encryption-key-at-least-32-chars',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
        )
        assert 'TRUSTED_HOSTS must be configured in production' in s.validate_secrets()

    def test_validate_secrets_rejects_short_custom_values(self):
        s = _settings(
            JWT_SECRET_KEY='short-jwt',
            ENCRYPTION_KEY='short-encryption',
            DB_PASSWORD='short-db',
            LFS_API_TOKEN='configured-lfs-token',
            TRUSTED_HOSTS=['api.example.com'],
        )

        issues = s.validate_secrets()

        assert 'JWT_SECRET_KEY must be at least 32 characters' in issues
        assert 'ENCRYPTION_KEY must be at least 32 characters' in issues
        assert 'DB_PASSWORD must be at least 16 characters' in issues

    def test_scu_cli_provider_requires_executable_path(self):
        issues = _settings(UNIVERSITY_AUTH_PROVIDER='scu_cli').validate_secrets()
        assert 'SCU_CLI_PATH is required when scu_cli authentication is enabled' in issues

    def test_mock_university_auth_is_rejected_in_production(self):
        issues = _settings(APP_ENV='prod', UNIVERSITY_AUTH_PROVIDER='mock').validate_secrets()
        assert 'UNIVERSITY_AUTH_PROVIDER cannot be mock in production' in issues
