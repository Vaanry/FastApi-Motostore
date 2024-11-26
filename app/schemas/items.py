from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    model: str
    cc: int = Field(0, ge=0)
    horsepower: int = Field(0, ge=0)
    age: str
    price: float = Field(0, ge=0)
    row: str


class CreateItem(ItemBase):
    pass


class ItemDB(ItemBase):
    id: int

    class Config:
        orm_mode = True
