from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.services.todos import TodoService, get_todo_service
from src.services.auth import get_current_user
from src.schemas.auth import CurrentUser
from src.schemas.todo import (
    TodoResponse,
    TodoSchema,
    TodoUpdateSchema,
    TodoUpdateStatusSchema,
)


router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
async def get_todos(
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await todo_service.get_todos(current_user.id, limit, offset)


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    name="Name Get todo by id",
    description="Desc Get todo by id",
    response_description="Todo details",
)
async def get_todo(
    todo_id: int,
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    todo = await todo_service.get_todo(todo_id, current_user.id)
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
async def create_todo(
    body: TodoSchema,
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await todo_service.create_todo(body, current_user.id)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    body: TodoUpdateSchema,
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    todo = await todo_service.update_todo(todo_id, current_user.id, body)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo_status(
    todo_id: int,
    body: TodoUpdateStatusSchema,
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    todo = await todo_service.update_status_todo(todo_id, current_user.id, body)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    await todo_service.remove_todo(todo_id, current_user.id)
    return None
