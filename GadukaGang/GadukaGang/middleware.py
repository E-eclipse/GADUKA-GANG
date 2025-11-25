"""
Middleware для логирования действий администраторов
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import AdminLog, ModeratorAction, SystemLog

User = get_user_model()


class AdminActionLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для автоматического логирования действий администраторов и модераторов.
    """
    
    # Список URL-путей, которые не нужно логировать
    EXCLUDED_PATHS = [
        '/admin/jsi18n/',
        '/static/',
        '/media/',
        '/login/',
        '/logout/',
        '/register/',
    ]
    
    # Список методов HTTP, которые нужно логировать
    LOGGED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def process_response(self, request, response):
        """
        Логирует действия администраторов и модераторов после обработки запроса.
        """
        # Проверяем, нужно ли логировать этот запрос
        if not self._should_log(request, response):
            return response
        
        user = request.user
        
        # Проверяем, является ли пользователь администратором или модератором
        if not user.is_authenticated:
            return response
        
        user_role = user.role
        
        # Определяем, нужно ли логировать действие
        if user_role in ['moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']:
            self._log_action(request, response, user, user_role)
        
        return response
    
    def _should_log(self, request, response):
        """
        Проверяет, нужно ли логировать этот запрос.
        """
        # Не логируем GET запросы (кроме специальных случаев)
        if request.method not in self.LOGGED_METHODS:
            return False
        
        # Не логируем исключенные пути
        path = request.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return False
        
        # Логируем только успешные запросы (2xx, 3xx)
        if not (200 <= response.status_code < 400):
            return False
        
        return True
    
    def _log_action(self, request, response, user, user_role):
        """
        Создает запись в логе действий.
        """
        try:
            # Определяем тип действия на основе метода и пути
            action_type = self._get_action_type(request)
            
            # Определяем тип ресурса
            resource_type = self._get_resource_type(request.path)
            
            # Получаем ID ресурса из запроса (если есть)
            resource_id = self._get_resource_id(request)
            
            description = f"{request.method} {request.path}"
            
            # Логируем в соответствующую таблицу
            if user_role == 'moderator':
                ModeratorAction.objects.create(
                    moderator=user,
                    action_type=action_type,
                    description=description,
                    target_type=resource_type,
                    target_id=resource_id or 0,
                )
            elif user_role in ['admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']:
                AdminLog.objects.create(
                    admin=user,
                    action_type=action_type,
                    description=description,
                    affected_resource_type=resource_type,
                    affected_resource_id=resource_id,
                )
            
            # Также логируем в общую таблицу SystemLog
            SystemLog.objects.create(
                user=user,
                action_type=action_type,
                action_level=user_role,
                description=description,
                affected_resource_type=resource_type,
                affected_resource_id=resource_id,
            )
        except Exception as e:
            # Не прерываем выполнение запроса, если логирование не удалось
            print(f"Ошибка при логировании действия: {e}")
    
    def _get_action_type(self, request):
        """
        Определяет тип действия на основе метода HTTP и пути.
        """
        method = request.method
        path = request.path.lower()
        
        # Маппинг путей к типам действий
        if '/admin/' in path:
            if 'delete' in path or method == 'DELETE':
                return 'delete_resource'
            elif 'edit' in path or 'change' in path or method == 'PUT' or method == 'PATCH':
                return 'update_resource'
            elif 'add' in path or method == 'POST':
                return 'create_resource'
        
        # Общий маппинг по методу
        action_map = {
            'POST': 'create_resource',
            'PUT': 'update_resource',
            'PATCH': 'update_resource',
            'DELETE': 'delete_resource',
        }
        
        return action_map.get(method, 'unknown_action')
    
    def _get_resource_type(self, path):
        """
        Определяет тип ресурса на основе пути.
        """
        path_lower = path.lower()
        
        if '/topic' in path_lower:
            return 'topic'
        elif '/post' in path_lower:
            return 'post'
        elif '/user' in path_lower or '/profile' in path_lower:
            return 'user'
        elif '/section' in path_lower:
            return 'section'
        elif '/admin' in path_lower:
            return 'admin_action'
        else:
            return 'unknown'
    
    def _get_resource_id(self, request):
        """
        Извлекает ID ресурса из запроса (из URL или POST данных).
        """
        # Пытаемся получить ID из URL (например, /topic/123/)
        path_parts = [p for p in request.path.split('/') if p]
        if path_parts:
            try:
                # Последняя часть пути может быть ID
                potential_id = int(path_parts[-1])
                return potential_id
            except (ValueError, IndexError):
                pass
        
        # Пытаемся получить ID из POST данных
        if request.method == 'POST' and hasattr(request, 'POST'):
            for key in ['id', 'pk', 'topic_id', 'post_id', 'user_id']:
                if key in request.POST:
                    try:
                        return int(request.POST[key])
                    except (ValueError, TypeError):
                        pass
        
        return None

