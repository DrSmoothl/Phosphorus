"""API response models."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base API response model."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Response data")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response model."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Response message")
    data: T = Field(..., description="Response data")


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Error response model."""

    error_code: str = Field(..., description="Error code")
    details: dict[str, Any] | None = Field(None, description="Error details")
