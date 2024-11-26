from pydantic import BaseModel


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
