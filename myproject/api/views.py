from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

from .auth import CookieJWTAuth
from .schemas import UserOut, LoginIn, TokenPairOut, ItemIn, ItemOut, RoleIn, UserCreate, RoleOut, ProfileOut, \
    ProfileUpdate, CategoryOut, ProductOut, ProductSchema, ProductSchema2, WishlistOut, WishlistIn, OrderSchema, \
    OrderSchemaOut, RoleAssignIn

from .models import Item, Category, Product, WishlistProduct, Wishlist, Order, OrderProduct, Role

from ninja.errors import HttpError
from ninja import Form, File, UploadedFile

from ninja_extra import NinjaExtraAPI, api_controller, route, permissions
from ninja_jwt.controller import NinjaJWTDefaultController, TokenVerificationController
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken


from ninja.responses import Response

from .permissions import IsManager, IsSuperUser

User = get_user_model()

api = NinjaExtraAPI(auth=[CookieJWTAuth()])
api.register_controllers(NinjaJWTDefaultController)
api.auth = [JWTAuth]


# =====================
# PUBLIC END-POINTS heh ;0 --- --- --- ПУБЛИЧНЫЕ ЭНД-ПОИНТЫ ДЛЯ РЕГИСТРАЦИИ И ВХОДА
# =====================
@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class AuthController:
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


# =====================
# AUTH END-POINTS heh ;0 --- --- --- АВТОРИЗОВАННЫЕ ЭНД-ПОИНТЫ
# =====================
@api_controller("/", auth=[JWTAuth()], permissions=[permissions.IsAuthenticated])
class UserController:

    # === Профиль ===
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

    # === Избранные товарЫ ===
    @route.get('users/me/wishlist', summary='Получить своё Избранное', response=List[WishlistOut])
    def get_wishlist(self, request):
        '''Получить вишлист, принадлежащий вошедшемоу в систему пользователю'''
        wishlist = get_object_or_404(Wishlist, user=request.user)
        return WishlistProduct.objects.filter(wishlist=wishlist.id)

    @route.post('users/me/wishlist', summary='Добавить Товар в своё избранное')
    def add_to_wishlist(self, request, payload: WishlistIn):
        """
        Если избранное существует, то функция добавляет в данный вишлист новую запись или обновляет ее, изменяя количество продукта.
        Если пользователь еще не имеет своего вишлиста, он будет автоматически создан перед добавлением/обновлением записи
        """
        if not Wishlist.objects.filter(user=request.user):
            Wishlist.objects.create(user=request.user)

        products = list()

        if WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user)):
            for wishlist_products in WishlistProduct.objects.filter(
                    wishlist=get_object_or_404(Wishlist, user=request.user)):
                products.append(wishlist_products.product.id)
            if payload.product in products:
                product = WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                         product=get_object_or_404(Product, id=payload.product))
                total_count = payload.count + product.values_list('count')[0][0]
                WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                               product=get_object_or_404(Product, id=payload.product)).update(
                    count=total_count)

                return "Запись была обновлена"
            else:
                WishlistProduct.objects.create(wishlist=get_object_or_404(Wishlist, user=request.user),
                                               product=get_object_or_404(Product, id=payload.product),
                                               count=payload.count)
                return "Запись была создана"
        else:
            WishlistProduct.objects.create(wishlist=get_object_or_404(Wishlist, user=request.user),
                                           product=get_object_or_404(Product, id=payload.product),
                                           count=payload.count)
            return "Запись была создана"

    @route.post('/wishlist/delete', summary='Удалить товар из своего избранного')
    def remove_from_wishlist(self, request, payload: WishlistIn):
        """
        Если...
        :param request:
        :param payload:
        :return:
        """
        products = list()

        if WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user)):
            for wishlist_products in WishlistProduct.objects.filter(
                    wishlist=get_object_or_404(Wishlist, user=request.user)):
                products.append(wishlist_products.product.id)
            if payload.product in products:
                product = WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                         product=get_object_or_404(Product, id=payload.product))
                if product.values_list('count')[0][0] > payload.count:
                    total_count = product.values_list('count')[0][0] - payload.count
                    WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                   product=get_object_or_404(Product, id=payload.product)).update(
                        count=total_count)
                    return "Запись была обновлена"
                else:
                    WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                   product=get_object_or_404(Product, id=payload.product)).delete()
                    return "Запись была удалена"

    # === Заказы ===
    @route.post('/order/add', summary='')
    def add_to_order(self, request, payload: WishlistIn):
        """

        :param request:
        :param payload:
        :return:
        """
        if not Order.objects.filter(user=request.user):
            Order.objects.create(user=request.user, status='new', total=0)
            order = get_object_or_404(Order, user=request.user)
        else:
            if Order.objects.filter(user=request.user, status='new'):
                order = Order.objects.filter(user=request.user, status='new').first()
            else:
                Order.objects.create(user=request.user, status='new', total=0)
                order = Order.objects.filter(user=request.user, status='new').first()

        products = list()

        if OrderProduct.objects.filter(order=order):
            for order_products in OrderProduct.objects.filter(order=order):
                products.append(order_products.product.id)
            if payload.product in products:
                product = OrderProduct.objects.filter(order=order,
                                                      product=get_object_or_404(Product, id=payload.product))
                total_count = payload.count + product.values_list('count')[0][0]
                OrderProduct.objects.filter(order=order,
                                            product=get_object_or_404(Product, id=payload.product)).update(
                    count=total_count)
                Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
                return "Запись была обновлена"
            else:
                product_price = Product.objects.filter(id=payload.product).values_list('price')[0][0]
                OrderProduct.objects.create(order=order,
                                            product=get_object_or_404(Product, id=payload.product),
                                            price=product_price,
                                            count=payload.count)
                Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
                return "Запись была создана"
        else:
            product_price = Product.objects.filter(id=payload.product).values_list('price')[0][0]
            OrderProduct.objects.create(order=order,
                                        product=get_object_or_404(Product, id=payload.product),
                                        price=product_price,
                                        count=payload.count)
            Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
            return "Запись была создана"

    @route.get('/order/{order_id}', summary='', response=List[OrderSchemaOut])
    def get_order_id(self, request, order_id: int):
        """

        :param request:
        :param order_id:
        :return:
        """
        order = get_object_or_404(Order, id=order_id)
        return OrderProduct.objects.filter(order=order.id)


@api_controller("/", auth=None, permissions=[permissions.AllowAny])
class PublicController:

    # === Категории ===
    @route.get('/categories', summary='Все категории...', response=List[CategoryOut])
    def list_of_categories(self, request):
        """Просмотр списка всех категорий товаров, хранящихся в базе данных"""
        return Category.objects.all()

    @route.get('/categories/{category_id}', summary='Получить категорию по id', response=CategoryOut)
    def get_category_to_id(self, request, category_id: int):
        """Получение информации о конкретной категории по ее slug-полю"""
        return get_object_or_404(Category, id=category_id)

    @route.get('/categories/{category_slug}', summary='Получить категорию по slug', response=CategoryOut)
    def get_category_to_slug(self, request, category_slug: str):
        """Получение информации о конкретной категории по ее slug-полю"""
        return get_object_or_404(Category, slug=category_slug)

    # === Продукты ===
    @route.get('/categories/filter/{category_id}', summary='Выбрать все товары из определённой категории по её id', response=List[ProductOut])
    def products_sorted_by_category(self, request, category_id: int):
        """Получение списка товаров, принадлежащих конкретной категории"""
        category = get_object_or_404(Category, id=category_id)
        products = Product.objects.filter(category=category)
        return products

    @route.get('/products', summary='Все товары', response=List[ProductOut])
    def list_of_products(self, request):
        """Просмотр списка всех товаров, хранящихся в базе данных"""
        return Product.objects.all()

    @route.get('/products/{product_id}', summary='Получить продукт по id', response=ProductOut)
    def get_product(self, request, product_id: int):
        """Получение информации о конкретном товаре по его id"""
        return get_object_or_404(Product, id=product_id)

    # === Сортировка ===
    @route.get('products/sorted/price_min', summary='Сортировать товары по убыванию цены', response=List[ProductSchema])
    def sorted_by_price_min(self, request):
        return Product.objects.order_by('-price')

    @route.get('products/sorted/price_max', summary='Сортировать товары по возрастанию цены', response=List[ProductSchema])
    def sorted_by_price_max(self, request):
        return Product.objects.order_by('price')

    @route.get('products/search/name', summary='Найти товар по названию', response=List[ProductSchema2])
    def search_by_name(self, request, name: str):
        return Product.objects.filter(title__icontains=name)

    @route.get('products/search/description', summary='Найти товар по описанию', response=List[ProductSchema2])
    def search_by_description(self, request, desc: str):
        return Product.objects.filter(description__icontains=desc)


# ============   ============   ============   ============   ============   ============   ============
#                                           Менеджер Контроль
# ============   ============   ============   ============   ============   ============   ============
@api_controller("/manager", auth=[JWTAuth()], permissions=[IsManager], tags=["Manager"])
class ManagerController:

    @route.get('/order', summary="Все заказы для менеджера", response=List[OrderSchemaOut])
    def list_all_orders(self, request):
        return Order.objects.all()

    @route.put('/order/{order_id}/status', summary='Менеджер меняет статус заказа')
    def update_order_status(self, request, order_id: int, status: str):
        if status in Order.STATUS:
            Order.objects.filter(id=order_id).update(status=status)
            return 'Статус заказа был изменен'
        else:
            raise HttpError(400, "Invalid status")


@api_controller("/items", auth=[JWTAuth()], permissions=[permissions.IsAuthenticated], tags=["Простые тестовые айтемы"])
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


@api_controller("/admin", auth=[JWTAuth()], permissions=[permissions.IsAuthenticated], tags=["Админские будни..."], )
class AdminController:
        @route.get("users", response=List[UserOut])
        def list_users(self, request):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            return User.objects.all()

        @route.get("roles", response=List[RoleOut], summary="Список всех ролей")
        def list_roles(self, request):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            return Role.objects.all()

        @route.get("roles/{role_id}", response=RoleOut, summary="Get role by ID")
        def get_role(self, request, role_id: int):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            return get_object_or_404(Role, id=role_id)

        @route.post("roles", response={201: RoleOut}, summary="Создать новую роль")
        def create_role(self, request, data: RoleIn):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            if Role.objects.filter(name=data.name).exists():
                raise HttpError(400, "Role with this name already exists")
            role = Role.objects.create(**data.dict())
            return 201, role

        @route.put("roles/{role_id}", response=RoleOut, summary="Изменить роль")
        def update_role(self, request, role_id: int, data: RoleIn):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            role = get_object_or_404(Role, id=role_id)
            # Обновляем только пришедшие поля
            for field, val in data.dict().items():
                setattr(role, field, val)
            role.save()
            return role

        @route.delete("roles/{role_id}", response=None, summary="Удалить роль")
        def delete_role(self, request, role_id: int):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            role = get_object_or_404(Role, id=role_id)
            role.delete()
            return 204, None

        # 2) Просмотр и управление ролями отдельного пользователя

        @route.get("users/{user_id}/roles", response=List[RoleOut], summary="Получить роли пользователя")
        def list_user_roles(self, request, user_id: int):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            user = get_object_or_404(User, id=user_id)
            return user.roles.all()

        @route.post("users/{user_id}/roles", response=List[RoleOut], summary="Указать роль пользователю")
        def assign_roles(self, request, user_id: int, data: RoleAssignIn):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            user = get_object_or_404(User, id=user_id)
            roles = list(Role.objects.filter(id__in=data.roles))
            if len(roles) != len(data.roles):
                raise HttpError(400, "One or more role IDs are invalid")
            user.roles.set(roles)
            return user.roles.all()

        @route.delete(
            "users/{user_id}/roles/{role_id}", response=None, summary="Убрать роль у пользователя")
        def remove_user_role(self, request, user_id: int, role_id: int):
            if not request.user.is_staff:
                raise HttpError(403, "Нет прав")
            user = get_object_or_404(User, id=user_id)
            role = get_object_or_404(Role, id=role_id)
            user.roles.remove(role)
            return 204, None


api.register_controllers(
    AuthController,
    PublicController,
    UserController,
    ManagerController,
    AdminController,
)
