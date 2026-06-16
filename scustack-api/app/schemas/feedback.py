from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    type: str = Field(max_length=20)
    content: str = Field(max_length=2000)
    email: str | None = Field(None, max_length=200)
