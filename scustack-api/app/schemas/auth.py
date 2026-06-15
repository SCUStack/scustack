from pydantic import BaseModel, Field, model_validator


class SmsSendRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')


class SmsVerifyRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')


class PasswordRegisterRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('passwords do not match')
        # Must contain at least 1 letter and 1 digit
        if not (any(c.isalpha() for c in self.password) and any(c.isdigit() for c in self.password)):
            raise ValueError('password must contain at least one letter and one digit')
        return self


class PasswordLoginRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r'^1\d{10}$')
    password: str = Field(min_length=1, max_length=128)
