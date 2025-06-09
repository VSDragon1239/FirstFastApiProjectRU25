from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404


from .auth import CookieJWTAuth
from .schemas import *

from .models import Role, Profile, FandomCategory, Fandom, TagCategory, Tag, Direction, Work, Chapter, Review, Rating

from ninja.responses import Response
from ninja import Form, File, UploadedFile
from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI, api_controller, route, permissions
from ninja_jwt.controller import NinjaJWTDefaultController, TokenVerificationController
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken



User = get_user_model()

api = NinjaExtraAPI(auth=[CookieJWTAuth()])
api.register_controllers(NinjaJWTDefaultController)
api.auth = [JWTAuth]


# =====================
# PUBLIC END-POINTS heh ;0 --- --- --- ПУБЛИЧНЫЕ ЭНД-ПОИНТЫ ДЛЯ РЕГИСТРАЦИИ И ВХОДА
# =====================
@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class AuthController:
    @route.post("register", response=UserOut)
    def register(self, request, data: UserCreate):
        user = User.objects.create_user(
            username=data.username,
            email=data.email,
            password=data.password
        )
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=[]
        )

    @route.post("login", response=TokenPairOut, auth=None, summary="Login with username & password")
    def login(self, request, data: LoginIn):
        """
        POST /api/auth/login    \n
        {                       \n
          "username": "Звезданутый Дракониус",   \n
          "password": "1239"    \n
        }                       \n
        → { "access": "...", "refresh": "..." }     \n

        :param request:         \n
        :param data:            \n
        :return:                \n
        """
        user = authenticate(username=data.username, password=data.password)
        if not user:
            raise HttpError(401, "Invalid credentials")

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # Формируем Response из ninja, а не из Django напрямую
        response = Response({"access": access, "refresh": str(refresh)})
        # Устанавливаем куки
        response.set_cookie("access_token", access, httponly=True, samesite="Lax")
        response.set_cookie("refresh_token", str(refresh), httponly=True, samesite="Lax")
        return response


# =====================
# PUBLIC END-POINTS heh ;0 --- --- --- ПУБЛИЧНЫЕ ЭНД-ПОИНТЫ
# =====================
@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class PublicController:

    @route.get("fandom-categories", response=List[FandomCategoryOut])
    def list_fandom_categories(self, request):
        return [FandomCategoryOut.from_orm(fc) for fc in FandomCategory.objects.all()]

    @route.get("fandom-categories/{cat_id}/fandoms", response=List[FandomOut])
    def list_fandoms(self, request, cat_id: int):
        cat = get_object_or_404(FandomCategory, pk=cat_id)
        return [FandomOut.from_orm(f) for f in cat.fandoms.all()]

    @route.get("tag-categories", response=List[TagCategoryOut])
    def list_tag_categories(self, request):
        return [TagCategoryOut.from_orm(tc) for tc in TagCategory.objects.all()]

    @route.get("tag-categories/{cat_id}/tags", response=List[TagOut])
    def list_tags(self, request, cat_id: int):
        tc = get_object_or_404(TagCategory, pk=cat_id)
        return [TagOut.from_orm(t) for t in tc.tags.all()]

    @route.get("directions", response=List[DirectionOut])
    def list_directions(self, request):
        return [DirectionOut.from_orm(d) for d in Direction.objects.all()]

    @route.get("works/list", response=List[WorkOut])
    def list_works(self, request):
        items = []
        for w in Work.objects.select_related("direction").prefetch_related("tags", "fandoms").all():
            items.append(WorkOut(
                id=w.id,
                name=w.name,
                rating_count=w.rating_count,
                rating=w.rating,
                direction=DirectionOut.from_orm(w.direction),
                tags=[TagOut.from_orm(t) for t in w.tags.all()],
                fandoms=[FandomOut.from_orm(f) for f in w.fandoms.all()],
            ))
        return items

    @route.get("works/{work_id}", response=WorkOut)
    def get_work(self, request, work_id: int):
        w = get_object_or_404(Work.objects.select_related("direction").prefetch_related("tags", "fandoms"), pk=work_id)
        return WorkOut(
            id=w.id,
            name=w.name,
            rating_count=w.rating_count,
            rating=w.rating,
            direction=DirectionOut.from_orm(w.direction),
            tags=[TagOut.from_orm(t) for t in w.tags.all()],
            fandoms=[FandomOut.from_orm(f) for f in w.fandoms.all()],
        )

    @route.get("works/{work_id}/chapters", response=List[ChapterOut])
    def list_chapters(self, request, work_id: int):
        qs = Chapter.objects.filter(work_id=work_id)
        return [
            ChapterOut(id=ch.id, work_id=ch.work_id, title=ch.title, file=request.build_absolute_uri(ch.file.url))
            for ch in qs
        ]

    @route.get("chapters/{ch_id}", response=ChapterOut)
    def get_chapter(self, request, ch_id: int):
        ch = get_object_or_404(Chapter, pk=ch_id)
        return ChapterOut(id=ch.id, work_id=ch.work_id, title=ch.title, file=request.build_absolute_uri(ch.file.url))


# =====================
# AUTH END-POINTS heh ;0 --- --- --- АВТОРИЗОВАННЫЕ ЭНД-ПОИНТЫ
# =====================
@api_controller("/", auth=[JWTAuth()], permissions=[permissions.IsAuthenticated])
class UserController:

    # ----- Профиль -----
    @route.get("users/me", response=UserOut)
    def me(self, request):
        user = request.user
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=[RoleOut.from_orm(r) for r in user.roles.all()]
        )

    @route.get("users/me/profile", response=ProfileOut)
    def get_profile(self, request):
        """
        GET /api/users/me/profile
        Возвращает avatar (URL) и description текущего пользователя.
        """
        prof = request.user.profile
        return ProfileOut(
            avatar=request.build_absolute_uri(prof.avatar.url) if prof.avatar else None,
            description=prof.description
        )

    @route.put("users/me/profile", response=ProfileOut)
    def update_profile(self, request, data: ProfileUpdate,  avatar: UploadedFile = File(None)):
        prof = request.user.profile
        if data.description is not None:
            prof.description = data.description
        if avatar:
            prof.avatar = avatar

        prof.save()
        return ProfileOut(
            avatar=request.build_absolute_uri(prof.avatar.url) if prof.avatar else None,
            description=prof.description
        )

    # ----- Роли -----
    @route.get("roles", response=List[RoleOut])
    def list_roles(self, request):
        return [RoleOut.from_orm(r) for r in Role.objects.all()]

    @route.post("roles", response=RoleOut)
    def create_role(self, request, data: RoleIn):
        role = Role.objects.create(**data.dict())
        return RoleOut.from_orm(role)

    @route.put("roles/{role_id}", response=RoleOut)
    def update_role(self, request, role_id: int, data: RoleIn):
        role = get_object_or_404(Role, pk=role_id)
        for f, v in data.dict().items():
            setattr(role, f, v)
        role.save()
        return RoleOut.from_orm(role)

    @route.delete("roles/{role_id}", response={204: None})
    def delete_role(self, request, role_id: int):
        role = get_object_or_404(Role, pk=role_id)
        role.delete()
        return 204, None

    # ----- Управление ролями пользователя -----
    @route.get("users/{user_id}/roles", response=List[RoleOut])
    def list_user_roles(self, request, user_id: int):
        u = get_object_or_404(User, pk=user_id)
        return [RoleOut.from_orm(r) for r in u.roles.all()]

    @route.post("users/{user_id}/roles", response=RoleOut)
    def add_user_role(self, request, user_id: int, data: RoleIn):
        if not request.user.is_staff:
            raise HttpError(403, "Только staff может выдавать роли")
        u = get_object_or_404(User, pk=user_id)
        role, _ = Role.objects.get_or_create(name=data.name)
        u.roles.add(role)
        return RoleOut.from_orm(role)

    @route.delete("users/{user_id}/roles/{role_id}", response={204: None})
    def remove_user_role(self, request, user_id: int, role_id: int):
        if not request.user.is_staff:
            raise HttpError(403, "Только staff может снимать роли")
        u = get_object_or_404(User, pk=user_id)
        role = get_object_or_404(Role, pk=role_id)
        u.roles.remove(role)
        return 204, None

    # # ----- CRUD для контента (пример для Work) -----
    # @route.post("works", response=WorkOut)
    # def create_work(self, request, data: WorkIn):
    #     w = Work.objects.create(
    #         author=request.user,
    #         name=data.name,
    #         direction_id=data.direction_id
    #     )
    #     w.tags.set(data.tag_ids)
    #     w.fandoms.set(data.fandom_ids)
    #     return WorkOut.from_orm(w)
    #


# =====================
# AUTHOR END-POINTS heh ;0 --- --- --- АВТОРСКИЕ ЭНД-ПОИНТЫ
# =====================
@api_controller(
    "/content",
    auth=[JWTAuth()],
    permissions=[permissions.IsAuthenticated],
)
class ContentController:

    @route.post("work/create", response=WorkOut)
    def create_work(self, request, data: WorkIn):
        """
        POST /api/works/
        {
          "name": "Новое произведение",
          "direction_id": 1,
          "tag_ids": [2,3],
          "fandom_ids": [1]
        }
        ➔ создаёт Work.author = request.user
        """
        w = Work.objects.create(
            author=request.user,
            name=data.name,
            rating=data.rating,
            direction_id=data.direction_id
        )
        w.tags.set(data.tag_ids)
        w.fandoms.set(data.fandom_ids)
        return WorkOut.from_orm(w)

    @route.put("works/{work_id}", response=WorkOut)
    def update_work(self, request, work_id: int, data: WorkIn):
        w = get_object_or_404(Work, pk=work_id, author=request.user)
        w.name = data.name
        w.direction_id = data.direction_id
        w.rating = data.rating
        w.tags.set(data.tag_ids)
        w.fandoms.set(data.fandom_ids)
        w.save()
        return WorkOut.from_orm(w)

    @route.delete("works/{work_id}", response={204: None})
    def delete_work(self, request, work_id: int):
        w = get_object_or_404(Work, pk=work_id, author=request.user)
        w.delete()
        return 204, None

    @route.get("", response=List[WorkOut])
    def list_my_works(self, request):
        """
        GET /api/works/
        ➔ список произведений текущего пользователя
        """
        qs = Work.objects.filter(author=request.user) \
                         .select_related("direction") \
                         .prefetch_related("tags", "fandoms")
        return [
            WorkOut(
                id=w.id,
                name=w.name,
                rating_count=w.rating_count,
                rating=w.rating,
                direction=DirectionOut.from_orm(w.direction),
                tags=[TagOut.from_orm(t) for t in w.tags.all()],
                fandoms=[FandomOut.from_orm(f) for f in w.fandoms.all()],
            ) for w in qs
        ]

    @route.post("/{work_id}/chapters", response=ChapterOut)
    def create_chapter(self, request, work_id: int, data: ChapterIn, file: UploadedFile = File(None)):
        """
        POST /api/works/{work_id}/chapters
        {
          "title": "Глава 1",
          "file": <файл>
        }
        ➔ создаёт Chapter.work = указанный work, проверяя, что вы — автор
        """
        w = get_object_or_404(Work, pk=work_id, author=request.user)
        ch = Chapter.objects.create(
            work=w,
            title=data.title,
            file=data.file  # UploadedFile из запроса
        )
        return ChapterOut(
            id=ch.id,
            work_id=ch.work_id,
            title=ch.title,
            file=request.build_absolute_uri(ch.file.url)
        )

    @route.get("/{work_id}/chapters", response=List[ChapterOut])
    def list_my_chapters(self, request, work_id: int):
        """
        GET /api/works/{work_id}/chapters
        ➔ список глав для вашего произведения
        """
        w = get_object_or_404(Work, pk=work_id, author=request.user)
        qs = w.chapters.all()
        return [
            ChapterOut(
                id=ch.id,
                work_id=ch.work_id,
                title=ch.title,
                file=request.build_absolute_uri(ch.file.url)
            ) for ch in qs
        ]


# =====================
# ADMIN END-POINTS heh ;0 --- --- --- АДМИНИСТРАТИВНЫЕ ЭНД-ПОИНТЫ
# =====================
@api_controller("/admin", auth=[JWTAuth()], permissions=[permissions.IsAuthenticated])
class AdminController:

    # --- Категории тегов ---
    @route.post("tag-categories", response=TagCategoryOut)
    def create_tag_category(self, request, data: TagCategoryIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        tc = TagCategory.objects.create(**data.dict())
        return TagCategoryOut.from_orm(tc)

    @route.put("tag-categories/{cat_id}", response=TagCategoryOut)
    def update_tag_category(self, request, cat_id: int, data: TagCategoryIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        tc = get_object_or_404(TagCategory, pk=cat_id)
        tc.name = data.name
        tc.save()
        return TagCategoryOut.from_orm(tc)

    @route.delete("tag-categories/{cat_id}", response={204: None})
    def delete_tag_category(self, request, cat_id: int):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        tc = get_object_or_404(TagCategory, pk=cat_id)
        tc.delete()
        return 204, None

    # --- Метки ---
    @route.post("tags", response=TagOut)
    def create_tag(self, request, data: TagIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        # убеждаемся, что категория существует
        category = get_object_or_404(TagCategory, pk=data.category_id)
        tag = Tag.objects.create(
            category=category,
            name=data.name,
            description=data.description
        )
        return TagOut(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            category=TagCategoryOut.from_orm(category)
        )

    @route.put("tags/{tag_id}", response=TagOut)
    def update_tag(self, request, tag_id: int, data: TagIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        tag = get_object_or_404(Tag, pk=tag_id)
        category = get_object_or_404(TagCategory, pk=data.category_id)
        tag.category = category
        tag.name = data.name
        tag.description = data.description
        tag.save()
        return TagOut(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            category=TagCategoryOut.from_orm(category)
        )

    @route.delete("tags/{tag_id}", response={204: None})
    def delete_tag(self, request, tag_id: int):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        tag = get_object_or_404(Tag, pk=tag_id)
        tag.delete()
        return 204, None

    # --- Категории фэндомов ---
    @route.post("fandom-categories", response=FandomCategoryOut)
    def create_fandom_category(self, request, data: FandomCategoryIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        fc = FandomCategory.objects.create(**data.dict())
        return FandomCategoryOut.from_orm(fc)

    @route.put("fandom-categories/{cat_id}", response=FandomCategoryOut)
    def update_fandom_category(self, request, cat_id: int, data: FandomCategoryIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        fc = get_object_or_404(FandomCategory, pk=cat_id)
        fc.name = data.name
        fc.save()
        return FandomCategoryOut.from_orm(fc)

    @route.delete("fandom-categories/{cat_id}", response={204: None})
    def delete_fandom_category(self, request, cat_id: int):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        fc = get_object_or_404(FandomCategory, pk=cat_id)
        fc.delete()
        return 204, None

    # --- Фэндомы ---
    @route.post("fandoms", response=FandomOut)
    def create_fandom(self, request, data: FandomIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        category = get_object_or_404(FandomCategory, pk=data.category_id)
        f = Fandom.objects.create(category=category, name=data.name)
        return FandomOut(
            id=f.id,
            name=f.name,
            category=FandomCategoryOut.from_orm(category)
        )

    @route.put("fandoms/{fandom_id}", response=FandomOut)
    def update_fandom(self, request, fandom_id: int, data: FandomIn):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        f = get_object_or_404(Fandom, pk=fandom_id)
        category = get_object_or_404(FandomCategory, pk=data.category_id)
        f.category = category
        f.name = data.name
        f.save()
        return FandomOut(
            id=f.id,
            name=f.name,
            category=FandomCategoryOut.from_orm(category)
        )

    @route.delete("fandoms/{fandom_id}", response={204: None})
    def delete_fandom(self, request, fandom_id: int):
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        f = get_object_or_404(Fandom, pk=fandom_id)
        f.delete()
        return 204, None

    @route.post("directions", response=DirectionOut)
    def create_direction(self, request, data: DirectionIn):
        """
        POST   /api/admin/directions
        Создаёт новое направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = Direction.objects.create(
            name=data.name,
            description=data.description or ""
        )
        return DirectionOut.from_orm(d)

    @route.put("directions/{dir_id}", response=DirectionOut)
    def update_direction(self, request, dir_id: int, data: DirectionIn):
        """
        PUT /api/admin/directions/{dir_id}
        Обновляет направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = get_object_or_404(Direction, pk=dir_id)
        d.name = data.name
        d.description = data.description or ""
        d.save()
        return DirectionOut.from_orm(d)

    @route.delete("directions/{dir_id}", response={204: None})
    def delete_direction(self, request, dir_id: int):
        """
        DELETE /api/admin/directions/{dir_id}
        Удаляет направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = get_object_or_404(Direction, pk=dir_id)
        d.delete()
        return (204, None)

    @route.post("ratings", response=RatingOut)
    def create_rating(self, request, data: RatingIn):
        """
        POST   /api/admin/directions
        Создаёт новое направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = Rating.objects.create(
            name=data.name,
            description=data.description or ""
        )
        return RatingOut.from_orm(d)

    @route.put("ratings/{dir_id}", response=RatingOut)
    def update_rating(self, request, dir_id: int, data: RatingIn):
        """
        PUT /api/admin/directions/{dir_id}
        Обновляет направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = get_object_or_404(Rating, pk=dir_id)
        d.name = data.name
        d.description = data.description or ""
        d.save()
        return RatingOut.from_orm(d)

    @route.delete("ratings/{dir_id}", response={204: None})
    def delete_rating(self, request, dir_id: int):
        """
        DELETE /api/admin/directions/{dir_id}
        Удаляет направление.
        """
        if not request.user.is_staff:
            raise HttpError(403, "Forbidden")
        d = get_object_or_404(Rating, pk=dir_id)
        d.delete()
        return 204, None

#
# =====================
# AUTH END-POINTS heh ;0 --- --- --- АВТОРИЗОВАННЫЕ ЭНД-ПОИНТЫ для группы... (УЖЕ НЕ НАДО!!!)
# =====================
# @api_controller("/users_groups",  auth=[JWTAuth()],  permissions=[permissions.IsAuthenticated]) # все эндпоинты требуют авторизации
# class UsersController:
#     @route.get("/{user_id}/groups", response=List[GroupOut])
#     def list_user_groups(self, request, user_id: int):
#         """
#         Список групп (ролей) пользователя
#         """
#         user = get_object_or_404(User, pk=user_id)
#         return [GroupOut(id=g.id, name=g.name) for g in user.groups.all()]
#
#     @route.post("/{user_id}/groups", response=GroupOut)
#     def add_group_to_user(self, request, user_id: int, data: GroupIn):
#         """
#         Назначить группу (роль) пользователю.
#         Доступно только staff (или superuser).
#         """
#         if not request.user.is_staff:
#             raise HttpError(403, "Forbidden: only staff can assign roles")
#         user = get_object_or_404(User, pk=user_id)
#         group, _ = Group.objects.get_or_create(name=data.name)
#         user.groups.add(group)
#         return GroupOut(id=group.id, name=group.name)
#
#     @route.delete("/{user_id}/groups/{group_id}", response={204: None, 404: None})
#     def remove_group_from_user(self, request, user_id: int, group_id: int):
#         """
#         Снять группу (роль) с пользователя.
#         Доступно только staff.
#         """
#         if not request.user.is_staff:
#             raise HttpError(403, "Forbidden: only staff can remove roles")
#         user = get_object_or_404(User, pk=user_id)
#         group = get_object_or_404(Group, pk=group_id)
#         user.groups.remove(group)
#         return 204, None
#
#     @route.get("/me/groups", response=List[GroupOut])
#     def my_groups(self, request):
#         """
#         Список групп текущего пользователя
#         """
#         return [GroupOut(id=g.id, name=g.name) for g in request.user.groups.all()]


# Чтобы было видно...
api.register_controllers(
    UserController,
    PublicController,
    AdminController,
    AuthController,
    ContentController,
)
