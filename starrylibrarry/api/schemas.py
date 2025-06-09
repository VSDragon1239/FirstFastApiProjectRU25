from ninja import Schema
from typing import List, Optional

from pydantic import EmailStr


# ----- Роли -----
class RoleIn(Schema):
    name: str
    description: Optional[str] = None


class RoleOut(Schema):
    id: int
    name: str
    description: Optional[str] = None


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


# ----- Фэндомы и теги -----
class FandomCategoryIn(Schema):
    name: str


class FandomIn(Schema):
    category_id: int
    name: str


class FandomCategoryOut(Schema):
    id: int
    name: str


class FandomOut(Schema):
    id: int
    name: str


class TagCategoryIn(Schema):
    name: str


class TagCategoryOut(Schema):
    id: int
    name: str


class TagIn(Schema):
    category_id: int
    name: str
    description: str


class TagOut(Schema):
    id: int
    name: str
    description: str


# ----- Направления -----
class DirectionOut(Schema):
    id: int
    name: str


# ----- Произведения -----
class WorkIn(Schema):
    name: str
    direction_id: int
    tag_ids: List[int]
    fandom_ids: List[int]


class WorkOut(Schema):
    id: int
    name: str
    rating_count: int
    direction: DirectionOut
    tags: List[TagOut]
    fandoms: List[FandomOut]


# ----- Главы -----
class ChapterIn(Schema):
    work_id: int
    title: str
    # file: File


class ChapterOut(Schema):
    id: int
    work_id: int
    title: str
    file: str    # URL


# ----- Отзывы -----
class ReviewIn(Schema):
    chapter_id: int
    # file: File


class ReviewOut(Schema):
    chapter_id: int
    user_id: int
    file: str
