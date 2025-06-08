from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

from .schemas import RegisterIn, UserOut, LoginIn, TokenPairOut, ItemIn, ItemOut, RoleIn

from .models import Item

from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI, api_controller, route, permissions
from ninja_jwt.controller import NinjaJWTDefaultController, TokenVerificationController
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken


User = get_user_model()

api = NinjaExtraAPI(auth=None)
api.register_controllers(NinjaJWTDefaultController)
api.auth = [JWTAuth()]


@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class PublicController:
    @route.get("test_full_data")
    def ping(self):
        return {"ping": "pong"}

    @route.get("hello")
    def hello(self):
        return {"message": "Hello, world!"}


# 4) Регистрация нового юзера
@api_controller("/auth", auth=None, permissions=[permissions.AllowAny])
class AuthController:
    @route.post("register", response={201: UserOut})
    def register(self, data: RegisterIn):
        if User.objects.filter(username=data.username).exists():
            raise HttpError(400, "Username already taken")
        user = User.objects.create(
            username=data.username,
            email=data.email,
            password=make_password(data.password)
        )
        return 201, user


@api_controller("/auth", auth=None, permissions=[permissions.AllowAny], tags=["Auth"],)
class CustomAuthController(TokenVerificationController):
    @route.post("login", response=TokenPairOut, auth=None, summary="Login with username & password")
    def login(self, request, data: LoginIn):
        """
        POST /api/auth/login    \n
        {                       \n
          "username": "ivan",   \n
          "password": "1234"    \n
        }                       \n
        → { "access": "...", "refresh": "..." }     \n

        :param request:         \n
        :param data:            \n
        :return:                \n
        """
        user = authenticate(username=data.username, password=data.password)
        if not user:
            raise HttpError(401, "Invalid credentials")
        # именно здесь генерим пару токенов
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        return {"access": access, "refresh": str(refresh)}


@api_controller("/users", permissions=[permissions.IsAdminUser], tags=["Users"],)
class UserController:
    @route.get("", response=List[UserOut])
    def list_users(self):
        return User.objects.all()

    @route.post("role", response=UserOut)
    def change_role(self, request, data: RoleIn):
        user = User.objects.filter(email=data.email).first()
        if not user:
            raise HttpError(404, "User not found")
        user.is_staff = data.is_staff
        user.save()
        return user


# 5) ItemController — защита JWT + права
@api_controller("/items", permissions=[permissions.IsAuthenticated])
class ItemController:

    @route.get("", response=List[ItemOut])
    def list_items(self):
        return Item.objects.all()

    @route.get("{item_id}", response=ItemOut)
    def get_item(self, item_id: int):
        return get_object_or_404(Item, pk=item_id)

    @route.post("", response={201: ItemOut}, permissions=[permissions.IsAdminUser])
    def create_item(self, data: ItemIn):
        item = Item.objects.create(**data.dict())
        return 201, item

    @route.put("{item_id}", response=ItemOut, permissions=[permissions.IsAdminUser])
    def update_item(self, item_id: int, data: ItemIn):
        item = get_object_or_404(Item, pk=item_id)
        for name, val in data.dict().items():
            setattr(item, name, val)
        item.save()
        return item

    @route.delete("{item_id}", response=None, permissions=[permissions.IsAdminUser])
    def delete_item(self, item_id: int):
        item = get_object_or_404(Item, pk=item_id)
        item.delete()
        return 204, None


api.register_controllers(
    PublicController,
    UserController,
    AuthController,
    CustomAuthController,
    ItemController
)
