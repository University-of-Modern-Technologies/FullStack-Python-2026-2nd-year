import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Environment variable {name} is required")
    return value


RABBITMQ_HOST = get_required_env("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = get_required_env("RABBITMQ_USER")
RABBITMQ_PASSWORD = get_required_env("RABBITMQ_PASSWORD")
RABBITMQ_VIRTUAL_HOST = get_required_env("RABBITMQ_VIRTUAL_HOST")
RABBITMQ_EXCHANGE = get_required_env("RABBITMQ_EXCHANGE")
RABBITMQ_QUEUE = get_required_env("RABBITMQ_QUEUE")
RABBITMQ_CONSUMER_NAME = os.getenv("RABBITMQ_CONSUMER_NAME", "Noname")

MONGODB_DB = get_required_env("MONGODB_DB")
MONGODB_HOST = get_required_env("MONGODB_HOST")
