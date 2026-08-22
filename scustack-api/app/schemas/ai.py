from pydantic import BaseModel, Field


class MaterialDraftRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=500)
    course_name: str | None = Field(default=None, max_length=200)
    semester: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, max_length=50)
    extracted_text: str | None = Field(default=None, max_length=20000)


class MaterialDraft(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=50)
    semester: str | None = Field(default=None, max_length=50)
    teacher: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    confidence: dict[str, float] = Field(default_factory=dict)


class MaterialDraftResponse(BaseModel):
    provider: str
    model: str
    draft: MaterialDraft


class AiProviderUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=8, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: str | None = Field(default=None, max_length=1000)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10000)


class AiProviderPublic(BaseModel):
    id: str
    name: str
    base_url: str
    model: str
    enabled: bool
    priority: int
    has_api_key: bool
    health: str = 'unknown'
    health_message: str | None = None
