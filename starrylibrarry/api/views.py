from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404

from .schemas import GroupOut, GroupIn, RegisterIn, UserOut, LoginIn

# from .models import Item

from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI, api_controller, route, permissions
from ninja_jwt.controller import NinjaJWTDefaultController, TokenVerificationController
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken


User = get_user_model()

api = NinjaExtraAPI(auth=None)
api.register_controllers(NinjaJWTDefaultController)
api.auth = [JWTAuth()]


# =====================
# PUBLIC END-POINTS heh ;0 --- --- --- ПУБЛИЧНЫЕ ЭНД-ПОИНТЫ
# =====================
@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class PublicController:
    @route.get("ping")
    def ping(self):
        return {"ping": "pong"}

    @route.get("hello")
    def hello(self):
        return {"message": "Hello, world!"}


# =====================
# AUTH END-POINTS heh ;0 --- --- --- АВТОРИЗОВАННЫЕ ЭНД-ПОИНТЫ для группы... (УЖЕ НЕ НАДО!!!)
# =====================
@api_controller("/users_groups",  auth=[JWTAuth()],  permissions=[permissions.IsAuthenticated]) # все эндпоинты требуют авторизации
class UsersController:
    @route.get("/{user_id}/groups", response=List[GroupOut])
    def list_user_groups(self, request, user_id: int):
        """
        Список групп (ролей) пользователя
        """
        user = get_object_or_404(User, pk=user_id)
        return [GroupOut(id=g.id, name=g.name) for g in user.groups.all()]

    @route.post("/{user_id}/groups", response=GroupOut)
    def add_group_to_user(self, request, user_id: int, data: GroupIn):
        """
        Назначить группу (роль) пользователю.
        Доступно только staff (или superuser).
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden: only staff can assign roles")
        user = get_object_or_404(User, pk=user_id)
        group, _ = Group.objects.get_or_create(name=data.name)
        user.groups.add(group)
        return GroupOut(id=group.id, name=group.name)

    @route.delete("/{user_id}/groups/{group_id}", response={204: None, 404: None})
    def remove_group_from_user(self, request, user_id: int, group_id: int):
        """
        Снять группу (роль) с пользователя.
        Доступно только staff.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden: only staff can remove roles")
        user = get_object_or_404(User, pk=user_id)
        group = get_object_or_404(Group, pk=group_id)
        user.groups.remove(group)
        return 204, None

    @route.get("/me/groups", response=List[GroupOut])
    def my_groups(self, request):
        """
        Список групп текущего пользователя
        """
        return [GroupOut(id=g.id, name=g.name) for g in request.user.groups.all()]


# Чтобы было видно...
api.register_controllers(
    PublicController,
    UsersController,
)
