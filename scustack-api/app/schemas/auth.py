from pydantic import BaseModel, Field


class SmsSendRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')


class SmsVerifyRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')
