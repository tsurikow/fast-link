import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.db.base_class import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                    server_default=func.now(),
                                                    nullable=False)
