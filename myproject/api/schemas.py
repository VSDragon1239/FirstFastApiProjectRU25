from pydantic import BaseModel
from ninja import Schema


from ninja import Schema


class RegisterIn(Schema):
    username: str
    email: str
    password: str


class UserOut(Schema):
    id: int
    username: str
    email: str
    class Config:
        orm_mode = True


class ItemIn(Schema):
    name: str
    price: float


class ItemOut(Schema):
    id: int
    name: str
    price: float
    class Config:
        orm_mode = True

