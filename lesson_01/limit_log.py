import logging
from datetime import time

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
)

handler_file = RotatingFileHandler(
    "rotation_app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
handler_file.setLevel(logging.INFO)

logger = logging.getLogger("my_logger")
logger.addHandler(handler_file)


handler_file_time = TimedRotatingFileHandler(
    "daily_app.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    atTime=time(2, 0),
)
logger.addHandler(handler_file_time)

logger.info("this is a info message")
