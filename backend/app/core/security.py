import uuid
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from backend.app.models.user import User
from backend.app.core.config import settings
from backend.app.core.manager import get_user_manager



def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    """
    Return a JWT strategy for creating and verifying tokens.
    """
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

# Define the token transport using Bearer scheme.
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

# Create an authentication backend by combining transport and strategy.
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_optional_active_user = fastapi_users.current_user(active=True, optional=True)
