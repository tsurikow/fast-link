import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.db.base_class import Base
from backend.app.models.url import URL, ExpiredURL


class User(SQLAlchemyBaseUserTableUUID, Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                    server_default=func.now(),
                                                    nullable=False)
    urls: Mapped[list["URL"]] = relationship("URL", secondary="user_urls", back_populates="users")
    expired_urls: Mapped[list["ExpiredURL"]] = relationship("ExpiredURL", secondary="user_expired_urls", back_populates="users")