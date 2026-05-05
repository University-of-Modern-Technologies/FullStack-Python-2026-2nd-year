from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.conf import constants
from src.conf import messages


class TodoSchema(BaseModel):
    title: str = Field(
        min_length=constants.TITLE_MIN_LENGTH,
        max_length=constants.TITLE_MAX_LENGTH,
        description=messages.todo_schema_title.get("ua"),
    )
    description: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
        description=messages.todo_schema_description,
    )
    completed: bool = Field(default=False, description=messages.todo_schema_completed)


class TodoUpdateSchema(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=constants.TITLE_MIN_LENGTH,
        max_length=constants.TITLE_MAX_LENGTH,
        description=messages.todo_schema_title.get("ua"),
    )
    description: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
        description=messages.todo_schema_description,
    )
    completed: Optional[bool] = Field(
        default=None, description=messages.todo_schema_completed
    )


class TodoUpdateStatusSchema(BaseModel):
    completed: bool


class TodoResponse(BaseModel):
    id: int = 1
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
