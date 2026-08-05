from app.core.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings(_env_file=None)
        assert s.APP_NAME == 'scustack-api'
        assert s.APP_ENV == 'dev'
        assert s.DEBUG is False
        assert s.DB_POOL_SIZE == 20

    def test_database_url(self):
        s = Settings()
        url = s.DATABASE_URL
        assert url.startswith('postgresql+asyncpg://')
        assert 'scustack:scustack@localhost' in url and '/scustack' in url

    def test_is_dev(self):
        s = Settings()
        assert s.is_dev is True

    def test_validate_secrets_reports_default_keys(self):
        s = Settings(
            JWT_SECRET_KEY='change-me-in-production',
            ENCRYPTION_KEY='change-me-in-production',
            DB_PASSWORD='scustack',
        )
        issues = s.validate_secrets()
        assert any('JWT_SECRET_KEY' in i for i in issues)
        assert any('ENCRYPTION_KEY' in i for i in issues)
        assert any('DB_PASSWORD' in i for i in issues)

    def test_validate_secrets_clean_when_keys_are_custom(self):
        s = Settings(
            JWT_SECRET_KEY='prod-secret-32chars-minimum!!',
            ENCRYPTION_KEY='prod-encrypt-32chars-minimum!',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
            TRUSTED_HOSTS=['api.example.com'],
        )
        issues = s.validate_secrets()
        assert len(issues) == 0

    def test_validate_secrets_includes_all_required_fields(self):
        s = Settings(
            JWT_SECRET_KEY='change-me-in-production',
            ENCRYPTION_KEY='change-me-in-production',
            DB_PASSWORD='scustack',
        )
        issues = s.validate_secrets()
        assert len(issues) == 4

    def test_validate_secrets_requires_default_lfs_token(self):
        s = Settings(
            JWT_SECRET_KEY='prod-secret-32chars-minimum!!',
            ENCRYPTION_KEY='prod-encrypt-32chars-minimum!',
            DB_PASSWORD='strong-db-password',
        )
        issues = s.validate_secrets()
        assert any('LFS_API_TOKEN' in issue for issue in issues)

    def test_validate_secrets_rejects_debug_in_production(self):
        s = Settings(
            APP_ENV='prod',
            DEBUG=True,
            JWT_SECRET_KEY='prod-secret-32chars-minimum!!',
            ENCRYPTION_KEY='prod-encrypt-32chars-minimum!',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
            TRUSTED_HOSTS=['api.example.com'],
        )
        assert 'DEBUG must be disabled in production' in s.validate_secrets()

    def test_validate_secrets_requires_trusted_hosts_in_production(self):
        s = Settings(
            APP_ENV='prod',
            JWT_SECRET_KEY='prod-secret-32chars-minimum!!',
            ENCRYPTION_KEY='prod-encrypt-32chars-minimum!',
            DB_PASSWORD='strong-db-password',
            LFS_API_TOKEN='configured-lfs-token',
        )
        assert 'TRUSTED_HOSTS must be configured in production' in s.validate_secrets()
