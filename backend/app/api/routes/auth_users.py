import uuid
from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from backend.app.core.manager import get_user_manager  # Your custom UserManager dependency
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate, UserDB
from backend.app.core.security import auth_backend  # Imported from your security.py

router = APIRouter()

# Initialize FastAPIUsers with your custom user manager, security backend, and schemas.
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

# Include authentication routes (login, token refresh, etc.)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Include registration route
router.include_router(
    fastapi_users.get_register_router(),
    prefix="/auth",
    tags=["auth"],
)

# Include user management routes (list, retrieve, update users)
router.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)

# Include the route for current user (e.g. /users/me)
router.include_router(
    fastapi_users.get_current_user_router(auth_backend),
    prefix="/users",
    tags=["users"],
)


# class RegisterRequest(BaseModel):
#     username: str
#     email: EmailStr
#     password: str
#

# @router.post("/login", summary="Login and obtain a JWT token")
# async def login(
#         form_data: OAuth2PasswordRequestForm = Depends(),
#         db: AsyncSession = Depends(get_session)
# ):
#     username = form_data.username
#     password = form_data.password
#
#     result = await db.execute(select(User).where(User.username == username))
#     user_obj = result.scalar_one_or_none()
#
#     if user_obj is None or not verify_password(password, user_obj.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#         )
#
#     access_token_expires = timedelta(minutes=30)
#     access_token = create_access_token(
#         data={"sub": str(user_obj.id)},  # Use the user’s UUID as a string
#         expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}
#
#
# @router.post("/register", summary="Register a new user", status_code=status.HTTP_201_CREATED)
# async def register(
#         register_data: RegisterRequest,
#         db: AsyncSession = Depends(get_session)
# ):
#     username = register_data.username
#     email = register_data.email
#     password = register_data.password
#
#     if username == "test":
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User already exists."
#         )
#
#     new_user = User(username=username, email=email, hashed_password=get_password_hash(password))
#     db.add(new_user)
#     await db.commit()
#     await db.refresh(new_user)
#
#     return {"message": "User registered successfully."}