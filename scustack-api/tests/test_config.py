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
        assert 'scustack:scustack@localhost:5432/scustack' in url

    def test_is_dev(self):
        s = Settings()
        assert s.is_dev is True
