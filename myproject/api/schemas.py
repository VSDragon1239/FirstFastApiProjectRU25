from pydantic import BaseModel
from ninja import Schema


class ItemIn(Schema):
    name: str
    price: float


class ItemOut(Schema):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True
