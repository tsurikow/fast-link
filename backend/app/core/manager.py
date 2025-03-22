import uuid

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager, UUIDIDMixin

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.core.security import get_password_hash
from backend.app.db.session import get_session
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request=None):
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request=None):
        logger.info(f"User {user.id} requested a password reset. Token: {token}")

    async def create(self, user_create: UserCreate, safe: bool = False, request=None) -> User:
        hashed_password = get_password_hash(user_create.password)
        user_create_data = user_create.dict()
        user_create_data["hashed_password"] = hashed_password
        user_create_data.pop("password", None)
        return await super().create(UserCreate(**user_create_data), safe=safe, request=request)

async def get_user_manager(session=Depends(get_session)):
    user_db = SQLAlchemyUserDatabase(session, User)
    yield UserManager(user_db)
