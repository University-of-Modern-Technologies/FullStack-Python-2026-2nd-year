"""Сервіс todos з Redis-кешем (тема 10)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.repository.todos import TodoRepository
from src.schemas.todo import TodoResponse, TodoSchema, TodoUpdateSchema, TodoUpdateStatusSchema
from src.services.cache import cache_service


class TodoService:
    """Координує бізнес-логіку todo та Redis-кешування списків."""
    def __init__(self, db: AsyncSession):
        """Ініціалізує екземпляр класу та його залежності."""
        self.todo_repository = TodoRepository(db)

    async def create_todo(self, body: TodoSchema, user_id: int):
        """Створює todo для поточного користувача."""
        todo = await self.todo_repository.create_todo(body, user_id)
        await cache_service.invalidate_user_todos(user_id)
        return todo

    async def get_todos(self, user_id: int, limit: int, offset: int):
        """Повертає сторінку todo поточного користувача."""
        cache_key = cache_service.todos_list_key(user_id, limit, offset)
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        todos = await self.todo_repository.get_todos(user_id, limit, offset)
        payload = [
            TodoResponse.model_validate(todo).model_dump(mode="json") for todo in todos
        ]
        await cache_service.set_json(
            cache_key, payload, settings.CACHE_TTL_SECONDS
        )
        return payload

    async def get_todo(self, todo_id: int, user_id: int):
        """Повертає один todo поточного користувача або None."""
        return await self.todo_repository.get_todo_by_id(todo_id, user_id)

    async def get_all_todos(self, limit: int, offset: int):
        """Повертає сторінку todo усіх користувачів для moderator/admin."""
        return await self.todo_repository.get_all_todos(limit, offset)

    async def update_todo(self, todo_id: int, user_id: int, body: TodoUpdateSchema):
        """Оновлює поля todo поточного користувача."""
        todo = await self.todo_repository.update_todo(todo_id, user_id, body)
        if todo is not None:
            await cache_service.invalidate_user_todos(user_id)
        return todo

    async def update_status_todo(
        self, todo_id: int, user_id: int, body: TodoUpdateStatusSchema
    ):
        """Оновлює статус виконання todo."""
        todo = await self.todo_repository.update_todo(todo_id, user_id, body)
        if todo is not None:
            await cache_service.invalidate_user_todos(user_id)
        return todo

    async def remove_todo(self, todo_id: int, user_id: int):
        """Видаляє todo з БД і повертає видалену модель."""
        todo = await self.todo_repository.remove_todo(todo_id, user_id)
        if todo is not None:
            await cache_service.invalidate_user_todos(user_id)
        return todo


async def get_todo_service(db: AsyncSession = Depends(get_db)) -> TodoService:
    """FastAPI dependency, що створює TodoService для запиту."""
    return TodoService(db)
