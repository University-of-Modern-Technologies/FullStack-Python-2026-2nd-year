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

    async def get_todos(self, limit: int, offset: int) -> Sequence[Todo]:
        stmt = select(Todo).offset(offset).limit(limit)
        todos = await self.db.execute(stmt)
        return todos.scalars().all()

    async def get_todo_by_id(self, todo_id: int) -> Todo | None:
        stmt = select(Todo).filter_by(id=todo_id)
        todo = await self.db.execute(stmt)
        return todo.scalar_one_or_none()

    async def create_todo(self, body: TodoSchema) -> Todo:
        todo = Todo(**body.model_dump())
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)
        return todo

    async def remove_todo(self, todo_id: int) -> Todo | None:
        todo = await self.get_todo_by_id(todo_id)
        if todo:
            await self.db.delete(todo)
            await self.db.commit()
        return todo

    async def update_todo(
        self, todo_id: int, body: TodoUpdateSchema | TodoUpdateStatusSchema
    ) -> Todo | None:
        todo = await self.get_todo_by_id(todo_id)
        if todo:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(todo, key, value)

            await self.db.commit()
            await self.db.refresh(todo)

        return todo
