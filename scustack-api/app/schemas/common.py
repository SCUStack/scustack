from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = 'ok'


class ErrorDetail(BaseModel):
    code: int
    data: None = None
    message: str
    detail: str | None = None


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    cursor: str | None = None


class ErrorCode:
    SUCCESS = 0
    BAD_REQUEST = 40000
    UNAUTHORIZED = 40100
    FORBIDDEN = 40300
    NOT_FOUND = 40400
    CONFLICT = 40900
    VALIDATION_ERROR = 42200
    INTERNAL_ERROR = 50000
    RATE_LIMITED = 42900
