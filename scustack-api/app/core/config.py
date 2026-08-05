from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'scustack-api'
    APP_ENV: Literal['dev', 'staging', 'prod'] = 'dev'
    DEBUG: bool = False
    SENTRY_DSN: str = ''
    PUBLIC_API_BASE: str = 'http://localhost:8403'
    TRUSTED_HOSTS: list[str] = []
    COOKIE_SECURE: bool | None = None

    _REQUIRED_IN_PRODUCTION: tuple[str, ...] = (
        'JWT_SECRET_KEY', 'ENCRYPTION_KEY', 'DB_PASSWORD',
    )

    CORS_ORIGINS: list[str] = ['http://localhost:3000']

    # Database
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'scustack'
    DB_PASSWORD: str = 'scustack'
    DB_NAME: str = 'scustack'
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str = 'redis://localhost:6379/0'
    REDIS_CONNECT_TIMEOUT_SECONDS: float = 0.2

    # Elasticsearch
    ES_HOST: str = 'http://localhost:9200'

    # Alibaba Cloud OSS
    OSS_ACCESS_KEY_ID: str = ''
    OSS_ACCESS_KEY_SECRET: str = ''
    OSS_ENDPOINT: str = ''
    OSS_BUCKET: str = ''

    STORAGE_DEFAULT_PROVIDER: Literal['lfs', 'oss'] = 'lfs'
    STORAGE_TARGET_REPLICA_COUNT: int = 1
    STORAGE_DOWNLOAD_GATEWAY: str = 'https://download.cacode.qzz.io'

    LFS_UPLOAD_URL: str = 'https://lfs.cacode.qzz.io/upload'
    LFS_PUBLIC_BASE: str = 'https://lfs.cacode.qzz.io'
    LFS_API_TOKEN: str = ''
    LFS_AUTH_HEADER: str = 'Authorization'
    LFS_AUTH_PREFIX: str = 'Bearer'
    LFS_UPLOAD_FIELD: str = 'file'

    # Encryption (AES-256-GCM for PII fields)
    ENCRYPTION_KEY: str = 'change-me-in-production'

    # JWT
    JWT_SECRET_KEY: str = 'change-me-in-production'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SMS
    SMS_ACCESS_KEY_ID: str = ''
    SMS_ACCESS_KEY_SECRET: str = ''
    SMS_SIGN_NAME: str = '川流课栈'
    SMS_TEMPLATE_CODE: str = ''

    # WeChat
    WECHAT_APP_ID: str = ''
    WECHAT_APP_SECRET: str = ''

    model_config = {'env_prefix': 'SCUSTACK_', 'env_file': '.env'}

    def validate_secrets(self) -> list[str]:
        """Check required secrets are not using default values. Returns list of issues."""
        issues: list[str] = []
        defaults = {
            'JWT_SECRET_KEY': 'change-me-in-production',
            'ENCRYPTION_KEY': 'change-me-in-production',
            'DB_PASSWORD': 'scustack',
        }
        for name in self._REQUIRED_IN_PRODUCTION:
            current = getattr(self, name, None)
            default = defaults.get(name)
            if current == default:
                issues.append(f'{name} is still set to default value')
        if self.STORAGE_DEFAULT_PROVIDER == 'lfs' and not self.LFS_API_TOKEN:
            issues.append('LFS_API_TOKEN is required when LFS is the default storage provider')
        if self.APP_ENV == 'prod' and self.DEBUG:
            issues.append('DEBUG must be disabled in production')
        if self.APP_ENV == 'prod' and not self.TRUSTED_HOSTS:
            issues.append('TRUSTED_HOSTS must be configured in production')
        return issues

    @property
    def DATABASE_URL(self) -> str:
        return (
            f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}'
            f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == 'dev'

    @property
    def session_cookie_secure(self) -> bool:
        return not self.is_dev if self.COOKIE_SECURE is None else self.COOKIE_SECURE


settings = Settings()
