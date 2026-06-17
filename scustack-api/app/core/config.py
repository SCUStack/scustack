from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'scustack-api'
    APP_ENV: Literal['dev', 'staging', 'prod'] = 'dev'
    DEBUG: bool = True
    SENTRY_DSN: str = ''

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

    # Elasticsearch
    ES_HOST: str = 'http://localhost:9200'

    # Alibaba Cloud OSS
    OSS_ACCESS_KEY_ID: str = ''
    OSS_ACCESS_KEY_SECRET: str = ''
    OSS_ENDPOINT: str = ''
    OSS_BUCKET: str = ''

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


settings = Settings()
