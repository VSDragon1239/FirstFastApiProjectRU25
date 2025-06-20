from ninja_extra.permissions import BasePermission


class IsManager(BasePermission):
    message = "Manager privileges required"

    def has_permission(self, request, controller) -> bool:
        """
        Вернёт True, если у request.user есть роль 'manager'.
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        # если на CustomUser.roles
        return user.roles.filter(name='manager').exists()
        # если Django-группы
        # return user.groups.filter(name='Менеджер').exists()


class IsSuperUser(BasePermission):
    message = "Superuser privileges required"

    def has_permission(self, request, controller) -> bool:
        """
            Вернёт True, если у request.user есть роль 'Полные права'.
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        # если на CustomUser.roles
        return user.roles.filter(name='Полные права').exists()
        # если Django-группы
        # return user.groups.filter(name='Менеджер').exists()
