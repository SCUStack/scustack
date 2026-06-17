from app.core.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.APP_NAME == 'scustack-api'
        assert s.APP_ENV == 'dev'
        assert s.DEBUG is True
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
        assert len(issues) == 3
