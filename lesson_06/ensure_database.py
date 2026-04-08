"""Створює PostgreSQL-базу з DB_NAME, якщо її ще немає. Запускати перед alembic upgrade."""

import os
import re

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

_user = os.getenv("USER")
_password = os.getenv("PASSWORD")
_host = os.getenv("HOST")
_port = os.getenv("PORT")
_db_name = os.getenv("DB_NAME")

_SAFE_IDENT = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def main() -> None:
    if not all((_user, _password, _host, _port, _db_name)):
        raise SystemExit("Заповни USER, PASSWORD, HOST, PORT, DB_NAME у .env")
    if not _SAFE_IDENT.match(_db_name):
        raise SystemExit("DB_NAME має бути простим ідентифікатором PostgreSQL (літери, цифри, _)")

    admin_uri = f"postgresql://{_user}:{_password}@{_host}:{_port}/postgres"
    engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": _db_name},
        ).scalar()
        if exists:
            print(f"База «{_db_name}» вже існує.")
            return
        conn.execute(text(f'CREATE DATABASE "{_db_name}"'))
        print(f"Створено базу «{_db_name}».")


if __name__ == "__main__":
    main()
