from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.todos import TodoService
from src.schemas.todo import (
    TodoResponse,
    TodoSchema,
    TodoUpdateSchema,
    TodoUpdateStatusSchema,
)


router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
async def get_todos(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    tod_service = TodoService(db)
    return await tod_service.get_todos(limit, offset)


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    name="Name Get todo by id",
    description="Desc Get todo by id",
    response_description="Todo details",
)
async def get_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    tod_service = TodoService(db)
    todo = await tod_service.get_todo(todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_todo(body: TodoSchema, db: AsyncSession = Depends(get_db)):
    tod_service = TodoService(db)
    return await tod_service.create_todo(body)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int, body: TodoUpdateSchema, db: AsyncSession = Depends(get_db)
):
    tod_service = TodoService(db)
    todo = await tod_service.update_todo(todo_id, body)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_status(
    todo_id: int, body: TodoUpdateStatusSchema, db: AsyncSession = Depends(get_db)
):
    tod_service = TodoService(db)
    todo = await tod_service.update_status_todo(todo_id, body)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    tod_service = TodoService(db)
    await tod_service.remove_todo(todo_id)
    return None
