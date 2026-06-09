"""Репозиторій SQL-операцій над todo-записами."""
import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Todo
from src.schemas.todo import TodoSchema, TodoUpdateSchema, TodoUpdateStatusSchema

logger = logging.getLogger("uvicorn.error")


class TodoRepository:
    """Інкапсулює SQL-запити для todo-сутностей."""
    def __init__(self, session: AsyncSession):
        """Ініціалізує екземпляр класу та його залежності."""
        self.db = session

    async def get_todos(self, user_id: int, limit: int, offset: int) -> Sequence[Todo]:
        """Повертає сторінку todo поточного користувача."""
        logger.info("DB hit: get_todos user_id=%s", user_id)
        stmt = select(Todo).where(Todo.user_id == user_id).offset(offset).limit(limit)
        todos = await self.db.execute(stmt)
        return todos.scalars().all()

    async def get_all_todos(self, limit: int, offset: int) -> Sequence[Todo]:
        """Повертає сторінку todo усіх користувачів для moderator/admin."""
        logger.info("DB hit: get_all_todos")
        stmt = select(Todo).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_todo_by_id(self, todo_id: int, user_id: int) -> Todo | None:
        """Шукає todo за id з обмеженням на власника."""
        stmt = select(Todo).filter_by(id=todo_id, user_id=user_id)
        todo = await self.db.execute(stmt)
        return todo.scalar_one_or_none()

    async def create_todo(self, body: TodoSchema, user_id: int) -> Todo:
        """Створює todo для поточного користувача."""
        todo = Todo(**body.model_dump(), user_id=user_id)
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)
        return todo

    async def remove_todo(self, todo_id: int, user_id: int) -> Todo | None:
        """Видаляє todo з БД і повертає видалену модель."""
        todo = await self.get_todo_by_id(todo_id, user_id)
        if todo:
            await self.db.delete(todo)
            await self.db.commit()
        return todo

    async def update_todo(
        self,
        todo_id: int,
        user_id: int,
        body: TodoUpdateSchema | TodoUpdateStatusSchema,
    ) -> Todo | None:
        """Оновлює поля todo поточного користувача."""
        todo = await self.get_todo_by_id(todo_id, user_id)
        if todo:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(todo, key, value)

            await self.db.commit()
            await self.db.refresh(todo)

        return todo
