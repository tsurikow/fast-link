from datetime import datetime
import re
from pydantic import BaseModel, field_validator, Field
from typing import Optional


class URLCreate(BaseModel):
    original_url: str


class URLResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None
    short_link: str | None = None

class URLCustomCreate(BaseModel):
    original_url: str
    short_code: str
    expiration: datetime = Field(
        ...,
        description="Enter expiration date without seconds (seconds will be ignored). Use ISO format."
    )
    fixed_expiration: bool = Field(
        False,
        description="Set to true if the link's expiration should remain fixed (not extended) on access."
    )

    @field_validator("expiration", mode="before")
    def remove_seconds(cls, value):
        if isinstance(value, datetime):
            return value.replace(second=0, microsecond=0)
        dt = datetime.fromisoformat(value)
        return dt.replace(second=0, microsecond=0)

    @field_validator("short_code")
    def validate_short_code(cls, value):
        if not re.match("^[A-Za-z0-9]+$", value):
            raise ValueError("short_code must contain only letters and numbers")
        return value

class URLUpdateRequest(BaseModel):
    original_url: Optional[str] = None