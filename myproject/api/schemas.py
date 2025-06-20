from typing import Optional, List

from ninja import Schema
from pydantic import EmailStr


# ----- Роли -----
class RoleIn(Schema):
    name: str
    description: Optional[str] = None


class RoleOut(Schema):
    id: int
    name: str
    description: Optional[str] = None


class RoleAssignIn(Schema):
    roles: List[int]


class GroupIn(Schema):
    name: str


class GroupOut(Schema):
    id: int
    name: str


# ----- Пользователь & Профиль -----
class LoginIn(Schema):
    username: str
    password: str


class TokenPairOut(Schema):
    access: str
    refresh: str


class UserCreate(Schema):
    username: str
    email: str
    password: str


class UserOut(Schema):
    id: int
    username: str
    email: EmailStr
    roles: List[RoleOut]

    class Config:
        orm_mode = True


class ProfileOut(Schema):
    avatar: Optional[str]       # URL до аватара
    description: Optional[str]


class ProfileUpdate(Schema):
    # avatar: Optional[File]      # загрузка нового файла
    description: Optional[str]


class ItemIn(Schema):
    name: str
    price: float


class ItemOut(Schema):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True


class CategoryIn(Schema):
    title: str


class CategoryOut(Schema):
    id: int
    title: str
    slug: str


class CategoryForProducts(Schema):
    title: str


class ProductIn(Schema):
    title: str
    category: int
    description: str
    price: float


class ProductOut(Schema):
    id: int
    title: str
    slug: str
    category: CategoryForProducts
    description: str
    price: float


class ProductSchema(Schema):
    title: str
    price: float


class ProductSchema2(Schema):
    title: str
    description: str
    price: float


class WishlistOut(Schema):
    product: ProductSchema
    count: int


class WishlistIn(Schema):
    product: int
    count: int = 1


class OrderSchema(Schema):
    id: int
    status: str
    total: float


class OrderSchemaOut(Schema):
    order: OrderSchema
    product: ProductSchema
    count: int
