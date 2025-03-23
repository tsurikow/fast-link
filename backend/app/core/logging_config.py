import sys
import uuid
import time
import logging
from fastapi import Request
from loguru import logger

class InterceptHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

# Replace the root logger's handlers with our InterceptHandler so that third-party logs are forwarded to Loguru.
logging.getLogger().handlers = [InterceptHandler()]

logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level="DEBUG")
logger.add("logs/app.log", format="{time} {level} {message}", level="DEBUG",
           rotation="10 MB", retention="10 days", compression="zip")


async def request_id_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    request.state.request_id = request_id
    logger.bind(request_id=request_id).info(f"Start request: {request.method} {request.url}")

    response = await call_next(request)
    duration = time.time() - start_time
    logger.bind(request_id=request_id).info(
        f"End request: {request.method} {request.url} completed in {duration:.3f} seconds"
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    return response