import asyncio
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.exc import ProgrammingError
from asyncpg.exceptions import UndefinedTableError

from backend.app.api.routes.auth_users import router as auth_users_router
from backend.app.api.routes.auth_users import fastapi_users, auth_backend
from backend.app.api.routes.urls import router as urls_router
from backend.app.core.config import settings
from backend.app.core.logging_config import request_id_timing
from backend.app.db.session import get_async_session
from backend.app.models.url import URL
from backend.app.services.expiration import move_expired_urls
from backend.app.services.cache import store_short_code

logger = logging.getLogger("fast-link")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Redis with active URL records (i.e. not expired)
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    try:
        try:
            now = datetime.now(timezone.utc)
            result = await session.execute(select(URL).where(
                (URL.expires_at == None) | (URL.expires_at > now)
            ))
            urls = result.scalars().all()
            for url in urls:
                await store_short_code(url.short_code, url.original_url)
            logger.info("Redis cache warmup completed with active URLs.")
        except (ProgrammingError, UndefinedTableError) as e:
            logger.warning(f"Could not warm up Redis cache: table 'urls' does not exist. {e}")
    finally:
        await session.close()

    # Start background task for moving expired URLs (and transferring relationships)
    async def expiration_task():
        while True:
            session_gen = get_async_session()
            session = await session_gen.__anext__()
            try:
                # Assume move_expired_urls now transfers associations
                expired_shortcodes = await move_expired_urls(session)
                if expired_shortcodes:
                    logger.info(f"Moved expired URLs and transferred relationships for codes: {expired_shortcodes}")
                    # Optionally, delete expired keys from Redis here if needed.
                    for code in expired_shortcodes:
                        await delete_cache(code)
                        logger.info(f"Deleted expired cache key: {code}")
            except (ProgrammingError, UndefinedTableError) as e:
                logger.warning(f"Expiration task skipped: table 'urls' does not exist. {e}")
            except Exception as e:
                logger.error(f"Error during expiration task: {e}")
            finally:
                await session.close()
            logger.info("Expiration task sleeping...")
            await asyncio.sleep(settings.EXPIRATION_CHECK_INTERVAL)
    task = asyncio.create_task(expiration_task())

    try:
        yield
    finally:
        task.cancel()

app = FastAPI(
    title="Fast-Link API",
    description="A FastAPI-based URL shortener service with user authentication.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_id_timing)

app.include_router(auth_users_router)
app.include_router(urls_router)

@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to Fast-Link API!"}

@app.get("/authenticated-route")
async def authenticated_route(user=Depends(fastapi_users.current_user(auth_backend))):
    return {"message": f"Hello {user.email}!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.FASTAPI_PORT, reload=True)
