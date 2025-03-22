import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base_class import Base


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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True),
                                                            ForeignKey("user.id"),
                                                            nullable=True)


class ExpiredURL(Base):
    """
    Model for storing URLs that have expired.
    When a URL expires, you can move it from the main URL table to this table.
    """
    __tablename__ = "expired_urls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    short_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    original_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True),
                                                            ForeignKey("user.id"),
                                                            nullable=True)
    moved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               nullable=False)
