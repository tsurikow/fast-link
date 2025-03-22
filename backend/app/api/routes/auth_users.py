import uuid

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from backend.app.core.manager import get_user_manager
from backend.app.core.security import auth_backend
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserDB, UserUpdate

router = APIRouter()

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserCreate, UserDB),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserDB, UserUpdate),
    prefix="/users",
    tags=["users"],
)
