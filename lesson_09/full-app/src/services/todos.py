from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository.todos import TodoRepository
from src.schemas.todo import TodoSchema, TodoUpdateSchema, TodoUpdateStatusSchema


class TodoService:
    def __init__(self, db: AsyncSession):
        self.todo_repository = TodoRepository(db)

    async def create_todo(self, body: TodoSchema, user_id: int):
        return await self.todo_repository.create_todo(body, user_id)

    async def get_todos(self, user_id: int, limit: int, offset: int):
        return await self.todo_repository.get_todos(user_id, limit, offset)

    async def get_todo(self, todo_id: int, user_id: int):
        return await self.todo_repository.get_todo_by_id(todo_id, user_id)

    async def update_todo(self, todo_id: int, user_id: int, body: TodoUpdateSchema):
        return await self.todo_repository.update_todo(todo_id, user_id, body)

    async def update_status_todo(
        self, todo_id: int, user_id: int, body: TodoUpdateStatusSchema
    ):
        return await self.todo_repository.update_todo(todo_id, user_id, body)

    async def remove_todo(self, todo_id: int, user_id: int):
        return await self.todo_repository.remove_todo(todo_id, user_id)


# async def get_todo_service(
#     db: Annotated[AsyncSession, Depends(get_db)],
# ) -> TodoService:
#     return TodoService(db)


async def get_todo_service(
    db: AsyncSession = Depends(get_db),
) -> TodoService:
    return TodoService(db)
