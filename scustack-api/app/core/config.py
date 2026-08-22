from pathlib import Path
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
    CSRF_COOKIE_DOMAIN: str | None = None

    AI_TIMEOUT_SECONDS: float = 30.0
    AI_MAX_INPUT_CHARS: int = 12000
    FILE_UPLOAD_SCAN_ENABLED: bool = False

    _REQUIRED_IN_PRODUCTION: tuple[str, ...] = (
        'JWT_SECRET_KEY',
        'ENCRYPTION_KEY',
        'DB_PASSWORD',
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
    STORAGE_DOWNLOAD_GATEWAY: str = 'https://download.cacodex.app'
    THUMBNAIL_DIR: Path = Path('data/thumbnails')
    PREVIEW_CACHE_DIR: Path = Path('data/previews')
    PREVIEW_CACHE_TTL_SECONDS: int = 900
    PREVIEW_CACHE_MAX_BYTES: int = 1024 * 1024 * 1024

    LFS_UPLOAD_URL: str = 'https://lfs.cacodex.app/upload'
    LFS_PUBLIC_BASE: str = 'https://lfs.cacodex.app'
    LFS_API_TOKEN: str = ''
    LFS_AUTH_HEADER: str = 'Authorization'
    LFS_AUTH_PREFIX: str = 'Bearer'
    LFS_UPLOAD_FIELD: str = 'file'
    LFS_PRIMARY_CHANNEL_NAME: str = 'SCUStack'
    LFS_BACKUP_CHANNEL_NAMES: list[str] = ['SCUStack2']

    # Encryption (AES-256-GCM for PII fields)
    ENCRYPTION_KEY: str = 'change-me-in-production'

    # JWT
    JWT_SECRET_KEY: str = 'change-me-in-production'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Sichuan University identity verification
    UNIVERSITY_AUTH_PROVIDER: Literal['disabled', 'mock', 'scu_cli'] = 'disabled'
    UNIVERSITY_AUTH_MOCK_PASSWORD: str = ''
    SCU_CLI_PATH: str = ''
    SCU_CLI_TIMEOUT_SECONDS: float = 30.0
    SCU_CLI_RUNTIME_DIR: str = ''

    model_config = {'env_prefix': 'SCUSTACK_', 'env_file': '.env'}

    def validate_secrets(self) -> list[str]:
        """Check required secrets are not using default values. Returns list of issues."""
        issues: list[str] = []
        defaults = {
            'JWT_SECRET_KEY': 'change-me-in-production',
            'ENCRYPTION_KEY': 'change-me-in-production',
            'DB_PASSWORD': 'scustack',
        }
        minimum_lengths = {
            'JWT_SECRET_KEY': 32,
            'ENCRYPTION_KEY': 32,
            'DB_PASSWORD': 16,
        }
        for name in self._REQUIRED_IN_PRODUCTION:
            current = getattr(self, name, '')
            default = defaults.get(name)
            if current == default:
                issues.append(f'{name} is still set to default value')
            elif len(current) < minimum_lengths[name]:
                issues.append(f'{name} must be at least {minimum_lengths[name]} characters')
        if self.STORAGE_DEFAULT_PROVIDER == 'lfs' and not self.LFS_API_TOKEN:
            issues.append('LFS_API_TOKEN is required when LFS is the default storage provider')
        if self.APP_ENV == 'prod' and self.DEBUG:
            issues.append('DEBUG must be disabled in production')
        if self.APP_ENV == 'prod' and not self.TRUSTED_HOSTS:
            issues.append('TRUSTED_HOSTS must be configured in production')
        if self.APP_ENV == 'prod' and self.UNIVERSITY_AUTH_PROVIDER == 'mock':
            issues.append('UNIVERSITY_AUTH_PROVIDER cannot be mock in production')
        if self.UNIVERSITY_AUTH_PROVIDER == 'scu_cli' and not self.SCU_CLI_PATH:
            issues.append('SCU_CLI_PATH is required when scu_cli authentication is enabled')
        if (
            self.APP_ENV == 'prod'
            and self.UNIVERSITY_AUTH_PROVIDER == 'scu_cli'
            and not self.SCU_CLI_RUNTIME_DIR
        ):
            issues.append('SCU_CLI_RUNTIME_DIR is required for scu_cli in production')
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
