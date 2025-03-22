import uuid
from fastapi import Depends
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from backend.app.models.user import User
from backend.app.schemas.user import UserDB
from backend.app.db.session import get_session

# Custom UserManager class
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = "SECRET_FOR_RESET"  # Replace with a secure secret in production
    verification_token_secret = "SECRET_FOR_VERIFY"    # Replace with a secure secret in production

    async def on_after_register(self, user: User, request=None):
        # You can add any custom logic here, like sending a welcome email
        print(f"User {user.id} has registered.")

# Dependency function for injecting UserManager
async def get_user_manager(session=Depends(get_session)):
    yield UserManager(session)