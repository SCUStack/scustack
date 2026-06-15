import random

from app.core.config import settings


class SmsClient:
    async def send_code(self, phone: str, code: str) -> bool:
        if settings.is_dev:
            print(f'[SMS DEV] To: {phone}  Code: {code}')
            return True

        # TODO: integrate Alibaba Cloud SMS SDK for staging/prod
        # client = AlibabaCloudClient(settings.SMS_ACCESS_KEY_ID, settings.SMS_ACCESS_KEY_SECRET)
        # return await client.send(phone, settings.SMS_SIGN_NAME, settings.SMS_TEMPLATE_CODE, {'code': code})
        return True


sms_client = SmsClient()


def generate_code() -> str:
    if settings.is_dev:
        return '000000'
    return ''.join(random.choices('0123456789', k=6))
