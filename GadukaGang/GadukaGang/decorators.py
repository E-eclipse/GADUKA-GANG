"""
Декораторы для проверки прав доступа на основе ролей пользователей
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test


def role_required(*allowed_roles):
    """
    Декоратор для проверки роли пользователя.
    
    Использование:
        @role_required('moderator', 'admin_level_1')
        def my_view(request):
            ...
    
    Args:
        *allowed_roles: Список разрешенных ролей
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Вы должны войти в систему для доступа к этой странице.')
                return redirect('account_login')
            
            # Суперпользователи и staff всегда имеют доступ
            if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
                return view_func(request, *args, **kwargs)
            
            user_role = getattr(request.user, 'role', 'user')
            
            # Определяем иерархию ролей
            role_hierarchy = {
                'user': 1,
                'moderator': 2,
                'admin_level_1': 3,
                'admin_level_2': 4,
                'admin_level_3': 5,
                'super_admin': 6,
            }
            
            # Проверяем, есть ли у пользователя одна из разрешенных ролей
            user_level = role_hierarchy.get(user_role, 0)
            allowed_levels = [role_hierarchy.get(role, 0) for role in allowed_roles]
            
            if user_level in allowed_levels or user_level >= max(allowed_levels, default=0):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'У вас нет прав для доступа к этой странице.')
            raise PermissionDenied
        
        return _wrapped_view
    return decorator


def moderator_required(view_func):
    """
    Декоратор для проверки прав модератора и выше.
    """
    return role_required('moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin')(view_func)


def admin_required(view_func):
    """
    Декоратор для проверки прав администратора (любого уровня) и выше.
    """
    return role_required('admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin')(view_func)


def admin_level_2_required(view_func):
    """
    Декоратор для проверки прав администратора уровня 2 и выше.
    """
    return role_required('admin_level_2', 'admin_level_3', 'super_admin')(view_func)


def admin_level_3_required(view_func):
    """
    Декоратор для проверки прав администратора уровня 3 и выше.
    """
    return role_required('admin_level_3', 'super_admin')(view_func)


def super_admin_required(view_func):
    """
    Декоратор для проверки прав главного администратора.
    """
    return role_required('super_admin')(view_func)

