from typing import List

from django.shortcuts import render, get_object_or_404
from ninja import NinjaAPI
from typing import List, Tuple
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

from ninja_extra import (
    NinjaExtraAPI, api_controller, route, permissions
)
from ninja_jwt.controller import NinjaJWTDefaultController

from .schemas import RegisterIn, UserOut, ItemIn, ItemOut
from .models import Item
from ninja_jwt.authentication import JWTAuth

from .schemas import ItemOut, ItemIn
from .models import Item

api = NinjaAPI()




User = get_user_model()

api = NinjaExtraAPI(
    auth=None,  # глобально — без авторизации (потом переопределим)
)

# 1) встраиваем JWT-контроллеры: /token/pair, /token/refresh, /token/verify
api.register_controllers(NinjaJWTDefaultController)


# 2) теперь задаём, что по умолчанию все методы (не в PublicController)
#    будут требовать JWT-авторизацию

api.auth = [JWTAuth()]


# 3) PublicController — всё public, без токена
@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class PublicController:
    @route.get("ping")
    def ping(self):
        return {"ping": "pong"}

    @route.get("hello")
    def hello(self):
        return {"message": "Hello, world!"}


# 4) Регистрация нового юзера — тоже public
@api_controller("/auth", auth=None, permissions=[permissions.AllowAny])
class AuthController:
    @route.post("register", response={201: UserOut})
    def register(self, data: RegisterIn):
        if User.objects.filter(username=data.username).exists():
            from ninja import HttpError
            raise HttpError(400, "Username already taken")
        user = User.objects.create(
            username=data.username,
            email=data.email,
            password=make_password(data.password)
        )
        return 201, user


# 5) ItemController — защита JWT + права
@api_controller(
    "/items",
    # здесь auth наследуется из api.auth = [JWTAuth()]
    permissions=[permissions.IsAuthenticated]
)
class ItemController:

    @route.get("", response=List[ItemOut])
    def list_items(self):
        return Item.objects.all()

    @route.get("{item_id}", response=ItemOut)
    def get_item(self, item_id: int):
        return get_object_or_404(Item, pk=item_id)

    @route.post(
        "", response={201: ItemOut},
        permissions=[permissions.IsAdminUser]  # только staff
    )
    def create_item(self, data: ItemIn):
        item = Item.objects.create(**data.dict())
        return 201, item

    @route.put(
        "{item_id}", response=ItemOut,
        permissions=[permissions.IsAdminUser]
    )
    def update_item(self, item_id: int, data: ItemIn):
        item = get_object_or_404(Item, pk=item_id)
        for name, val in data.dict().items():
            setattr(item, name, val)
        item.save()
        return item

    @route.delete(
        "{item_id}", response=None,
        permissions=[permissions.IsAdminUser]
    )
    def delete_item(self, item_id: int):
        item = get_object_or_404(Item, pk=item_id)
        item.delete()
        return 204, None


api.register_controllers(
    PublicController,
    AuthController,
    ItemController
)
