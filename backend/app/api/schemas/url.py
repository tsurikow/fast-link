from datetime import datetime

from pydantic import BaseModel


class URLCreate(BaseModel):
    original_url: str


class URLResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None
    short_link: str | None = None
