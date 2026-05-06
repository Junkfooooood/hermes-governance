"""Unified API response models."""

from typing import Any, Optional

from pydantic import BaseModel


class Meta(BaseModel):
    request_id: str
    timestamp: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}


class ApiResponse(BaseModel):
    data: Any
    meta: Meta


class ErrorResponse(BaseModel):
    error: ErrorDetail
    meta: Meta
