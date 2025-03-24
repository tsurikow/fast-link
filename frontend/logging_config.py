from loguru import logger

logger.remove()
logger.add("stdout", format="{time} {level} {message}", level="DEBUG")
logger.add(
    "app.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
)