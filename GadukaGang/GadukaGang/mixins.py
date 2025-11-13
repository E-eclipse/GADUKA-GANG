"""
Mixins для class-based views для проверки прав доступа на основе ролей
"""
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect


class RoleRequiredMixin:
    """
    Mixin для проверки роли пользователя в class-based views.
    
    Использование:
        class MyView(RoleRequiredMixin, View):
            allowed_roles = ['moderator', 'admin_level_1']
    """
    allowed_roles = []
    permission_denied_message = 'У вас нет прав для доступа к этой странице.'
    raise_exception = False
    
    def get_role_hierarchy(self):
        """Возвращает словарь иерархии ролей"""
        return {
            'user': 1,
            'moderator': 2,
            'admin_level_1': 3,
            'admin_level_2': 4,
            'admin_level_3': 5,
            'super_admin': 6,
        }
    
    def has_role_permission(self):
        """Проверяет, есть ли у пользователя необходимая роль"""
        if not self.request.user.is_authenticated:
            return False
        
        if not self.allowed_roles:
            return True  # Если роли не указаны, разрешаем доступ
        
        user_role = self.request.user.role
        role_hierarchy = self.get_role_hierarchy()
        
        user_level = role_hierarchy.get(user_role, 0)
        allowed_levels = [role_hierarchy.get(role, 0) for role in self.allowed_roles]
        
        # Пользователь имеет доступ, если его уровень >= минимального разрешенного
        return user_level in allowed_levels or user_level >= max(allowed_levels, default=0)
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_role_permission():
            if self.raise_exception:
                raise PermissionDenied(self.permission_denied_message)
            messages.error(request, self.permission_denied_message)
            return redirect('account_login')
        return super().dispatch(request, *args, **kwargs)


class ModeratorRequiredMixin(RoleRequiredMixin):
    """Mixin для проверки прав модератора и выше"""
    allowed_roles = ['moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin для проверки прав администратора (любого уровня) и выше"""
    allowed_roles = ['admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']


class AdminLevel2RequiredMixin(RoleRequiredMixin):
    """Mixin для проверки прав администратора уровня 2 и выше"""
    allowed_roles = ['admin_level_2', 'admin_level_3', 'super_admin']


class AdminLevel3RequiredMixin(RoleRequiredMixin):
    """Mixin для проверки прав администратора уровня 3 и выше"""
    allowed_roles = ['admin_level_3', 'super_admin']


class SuperAdminRequiredMixin(RoleRequiredMixin):
    """Mixin для проверки прав главного администратора"""
    allowed_roles = ['super_admin']

