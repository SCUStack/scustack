from pydantic import BaseModel, Field, model_validator

UNIVERSITY_ID_PATTERN = r'^\d{8,14}$'


class UniversityRegisterRequest(BaseModel):
    university_id: str = Field(min_length=8, max_length=14, pattern=UNIVERSITY_ID_PATTERN)
    university_password: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode='after')
    def validate_local_password(self):
        if self.password != self.confirm_password:
            raise ValueError('passwords do not match')
        if not (
            any(char.isalpha() for char in self.password)
            and any(char.isdigit() for char in self.password)
        ):
            raise ValueError('password must contain at least one letter and one digit')
        return self


class PasswordLoginRequest(BaseModel):
    university_id: str = Field(min_length=8, max_length=14, pattern=UNIVERSITY_ID_PATTERN)
    password: str = Field(min_length=1, max_length=128)
