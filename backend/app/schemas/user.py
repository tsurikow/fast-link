from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None

    def create_update_dict(self) -> dict:
        return {key: value for key, value in self.dict().items() if value is not None}


class UserDB(UserBase):
    id: UUID
    registered_at: datetime

    model_config = {
        "from_attributes": True,
    }
