from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.todos import TodoRepository
from src.schemas.todo import TodoSchema, TodoUpdateSchema, TodoUpdateStatusSchema


class TodoService:
    def __init__(self, db: AsyncSession):
        self.todo_repository = TodoRepository(db)

    async def create_todo(self, body: TodoSchema):
        # More code
        return await self.todo_repository.create_todo(body)

    async def get_todos(self, limit: int, offset: int):
        return await self.todo_repository.get_todos(limit, offset)

    async def get_todo(self, todo_id: int):
        return await self.todo_repository.get_todo_by_id(todo_id)

    async def update_todo(self, todo_id: int, body: TodoUpdateSchema):
        return await self.todo_repository.update_todo(todo_id, body)

    async def update_status_todo(self, todo_id: int, body: TodoUpdateStatusSchema):
        return await self.todo_repository.update_todo(todo_id, body)

    async def remove_todo(self, todo_id: int):
        return await self.todo_repository.remove_todo(todo_id)
