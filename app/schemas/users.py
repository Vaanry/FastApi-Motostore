from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str
    password: str


class CreateUser(UserBase):
    pass


class User(BaseModel):
    id: int
    username: str
    tg_id: Optional[int] = None
    reg_date: datetime
    balance: float = Field(default=0, ge=0)
    is_admin: bool = Field(default=False, alias="is_admin")
    active: bool = Field(default=True, alias="is_active")

    class Config:
        orm_mode = True
