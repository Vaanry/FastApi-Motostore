from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderBase(BaseModel):
    timestamp: datetime
    tg_id: Optional[int] = None
    quantity: int = Field(default=0, ge=0)
    model: str
    cc: Optional[int] = None
    horsepower: Optional[int] = None
    age: Optional[str] = None
    purchase: float = Field(default=0, ge=0)
    is_paid: bool = Field(default=False)
    order_archive: Optional[str] = None


class OrderDB(OrderBase):
    id: int

    class Config:
        orm_mode = True
