from ninja import Schema
from pydantic import EmailStr


class GroupIn(Schema):
    name: str


class GroupOut(Schema):
    id: int
    name: str


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
