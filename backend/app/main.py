import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from backend.app.api.routes.auth_users import router as auth_users_router
from backend.app.api.routes.urls import router as urls_router
from backend.app.core.config import settings
from backend.app.core.logging_config import add_request_id
from backend.app.db.session import get_session
from backend.app.models.url import URL
from backend.app.services.expiration import move_expired_urls  # Function to move expired URLs
from backend.app.services.shortener import store_short_code


@asynccontextmanager
async def lifespan(app: FastAPI):
    async for session in get_session():
        result = await session.execute(select(URL))
        urls = result.scalars().all()
        for url in urls:
            await store_short_code(url.short_code, url.original_url)
        break

    async def expiration_task():
        while True:
            async for session in get_session():
                await move_expired_urls(session)
                break
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

app.middleware("http")(add_request_id)

app.include_router(auth_users_router)
app.include_router(urls_router)

@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to Fast-Link API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.FASTAPI_PORT, reload=True)
