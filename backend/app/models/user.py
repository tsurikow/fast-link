import uuid
from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.db.base_class import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                    server_default=func.now(),
                                                    nullable=False)