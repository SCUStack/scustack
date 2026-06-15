import hashlib
import secrets

from app.core.config import settings


class SmsClient:
    async def send_code(self, phone: str, code: str) -> bool:
        if settings.is_dev:
            print(f'[SMS DEV] To: ***{phone[-4:]}  Code: {code}')
            return True

        # TODO: integrate Alibaba Cloud SMS SDK for staging/prod
        return True


sms_client = SmsClient()


def generate_code() -> str:
    if settings.is_dev:
        return '000000'
    return f'{secrets.randbelow(10**6):06d}'


def hash_code(code: str, phone: str) -> str:
    """Hash verification code with phone as salt."""
    return hashlib.sha256(f'{code}:{phone}:scustack-sms'.encode()).hexdigest()
