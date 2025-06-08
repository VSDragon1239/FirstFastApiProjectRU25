from ninja import Schema
from pydantic import EmailStr


class RegisterIn(Schema):
    username: str
    email: EmailStr
    password: str


class UserOut(Schema):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True


class LoginIn(Schema):
    username: str
    password: str


class TokenPairOut(Schema):
    access: str
    refresh: str


class ItemIn(Schema):
    name: str
    price: float


class ItemOut(Schema):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True


class RoleIn(Schema):
    email: EmailStr
    is_staff: bool
