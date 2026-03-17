import logging

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("my_logger")
logger.setLevel(logging.WARNING)

file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


logger.debug("this is a debug message")
logger.info("this is an info message")
logger.warning("this is a warning message")
logger.error("this is an error message")
logger.critical("this is a critical message")
