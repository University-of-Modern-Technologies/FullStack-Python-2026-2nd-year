"""Тема 10: slowapi — обмеження запитів за IP клієнта."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
