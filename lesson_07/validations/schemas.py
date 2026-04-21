from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class OwnerSchema(BaseModel):
    fullname: str
    email: EmailStr


class OwnerResponse(BaseModel):
    id: int = 1
    fullname: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class CatSchema(BaseModel):
    nick: str = Field("Myrzik", min_length=3, max_length=20)
    age: int = Field(1, ge=1, le=20)  # ge - greater than, le - less than
    vaccinated: Optional[bool] = False
    owner_id: int = Field(1, ge=1)


class CatResponse(BaseModel):
    id: int = 1
    nick: str
    age: int
    vaccinated: bool
    owner_id: int
    model_config = ConfigDict(from_attributes=True)
