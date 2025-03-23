import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.db.base_class import Base
from backend.app.models.user import User

class UserURL(Base):
    __tablename__ = "user_urls"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    url_id: Mapped[str] = mapped_column(
        String, ForeignKey("urls.id"), primary_key=True
    )

class UserExpiredURL(Base):
    __tablename__ = "user_expired_urls"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    url_id: Mapped[str] = mapped_column(
        String, ForeignKey("expired_urls.id"), primary_key=True
    )

class URL(Base):
    """
    Model for storing shortened URLs.
    """
    __tablename__ = "urls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    short_code: Mapped[str] = mapped_column(String, unique=True,
                                            nullable=False,
                                            index=True)
    original_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_urls",
        back_populates="urls"
    )


class ExpiredURL(URL):
    """
    Model for storing URLs that have expired.
    When a URL expires, you can move it from the main URL table to this table.
    """
    __tablename__ = "expired_urls"
    __mapper_args__ = {"concrete": True}

    moved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               nullable=False)
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_expired_urls",
        back_populates="expired_urls"
    )