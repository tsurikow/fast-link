import sys
import uuid

from fastapi import Request
from loguru import logger

# Configure Loguru
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
logger.add("logs/app.log", format="{time} {level} {message}", level="INFO",
           rotation="10 MB", retention="10 days", compression="zip")

# Middleware to add a request id
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    logger.bind(request_id=request_id).info("Start request")
    response = await call_next(request)
    logger.bind(request_id=request_id).info("End request")
    response.headers["X-Request-ID"] = request_id
    return response
