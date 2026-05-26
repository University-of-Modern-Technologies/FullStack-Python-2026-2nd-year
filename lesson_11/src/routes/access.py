"""Тема 10: RBAC — один router, різні Depends за роллю."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.schemas.auth import CurrentUser
from src.schemas.user import UserResponse, UserRoleUpdate
from src.schemas.todo import TodoResponse
from src.services.users import UsersService, get_users_service
from src.services.auth import (
    get_current_admin_user,
    get_current_moderator_user,
    get_current_user,
)
from src.services.todos import TodoService, get_todo_service

router = APIRouter(prefix="/access", tags=["access"])


@router.get("/user")
async def user_scope(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Будь-який авторизований користувач."""
    return {
        "scope": "user",
        "message": "Доступ для user / moderator / admin",
        "current_user": current_user,
    }


@router.get("/moderator/todos", response_model=list[TodoResponse])
async def moderator_scope(
    todo_service: Annotated[TodoService, Depends(get_todo_service)],
    _moderator: Annotated[CurrentUser, Depends(get_current_moderator_user)],
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Moderator або admin — усі todos."""
    return await todo_service.get_all_todos(limit, offset)


@router.get("/admin/users", response_model=list[UserResponse])
async def admin_list_users(
    users_service: Annotated[UsersService, Depends(get_users_service)],
    _admin: Annotated[CurrentUser, Depends(get_current_admin_user)],
):
    """Лише admin."""
    return await users_service.list_users()


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse)
async def admin_change_role(
    user_id: int,
    body: UserRoleUpdate,
    users_service: Annotated[UsersService, Depends(get_users_service)],
    _admin: Annotated[CurrentUser, Depends(get_current_admin_user)],
):
    """Лише admin."""
    user = await users_service.update_role(user_id, body.role)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
