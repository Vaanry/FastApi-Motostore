from datetime import datetime
from pydantic import BaseModel, Field


class ManufacturerBase(BaseModel):
    name: str
    country: str


class CreateManufacturer(ManufacturerBase):
    pass


class ManufacturerDB(ManufacturerBase):
    id: int

    class Config:
        orm_mode = True


class ModelBase(BaseModel):
    manufacturer: str
    type: str
    model: str


class CreateModel(ModelBase):
    pass


class ModelDB(ModelBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    password: str


class CreateUser(UserBase):
    pass


class User(BaseModel):
    id: int
    reg_date: datetime
    balance: int = Field(None, ge=0)
    is_admin: bool = Field(False, alias="is-admin")
    active: bool = Field(True, alias="is-active")

    class Config:
        orm_mode = True
