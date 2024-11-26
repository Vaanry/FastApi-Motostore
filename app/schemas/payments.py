from datetime import datetime

from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    timestamp: datetime
    tg_id: int
    amount: float = Field(default=0, ge=0)
    uuid: str
    confirmed: bool = Field(default=False)


class PaymentDB(PaymentBase):
    id: int

    class Config:
        orm_mode = True
