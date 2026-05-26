import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Todo
from src.schemas.todo import TodoSchema, TodoUpdateSchema, TodoUpdateStatusSchema

logger = logging.getLogger("uvicorn.error")


class TodoRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_todos(self, user_id: int, limit: int, offset: int) -> Sequence[Todo]:
        logger.info("DB hit: get_todos user_id=%s", user_id)
        stmt = select(Todo).where(Todo.user_id == user_id).offset(offset).limit(limit)
        todos = await self.db.execute(stmt)
        return todos.scalars().all()

    async def get_all_todos(self, limit: int, offset: int) -> Sequence[Todo]:
        logger.info("DB hit: get_all_todos")
        stmt = select(Todo).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_todo_by_id(self, todo_id: int, user_id: int) -> Todo | None:
        stmt = select(Todo).filter_by(id=todo_id, user_id=user_id)
        todo = await self.db.execute(stmt)
        return todo.scalar_one_or_none()

    async def create_todo(self, body: TodoSchema, user_id: int) -> Todo:
        todo = Todo(**body.model_dump(), user_id=user_id)
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)
        return todo

    async def remove_todo(self, todo_id: int, user_id: int) -> Todo | None:
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
        todo = await self.get_todo_by_id(todo_id, user_id)
        if todo:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(todo, key, value)

            await self.db.commit()
            await self.db.refresh(todo)

        return todo
