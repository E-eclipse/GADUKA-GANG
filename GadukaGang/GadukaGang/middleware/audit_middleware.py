"""
Audit middleware for tracking user actions and data changes
"""
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from GadukaGang.models import SystemLog

User = get_user_model()


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive audit logging
    Tracks user actions, IP addresses, and user agents
    """
    
    # Actions that should be logged
    LOGGED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/__debug__/',
    ]
    
    def process_request(self, request):
        """Store request start time and user info"""
        # Skip if path is excluded
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return None
        
        # Store request metadata
        request._audit_data = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'method': request.method,
            'path': request.path,
        }
        
        return None
    
    def process_response(self, request, response):
        """Log the request if it's a modifying action"""
        # Skip if no audit data or path is excluded
        if not hasattr(request, '_audit_data'):
            return response
        
        # Only log modifying actions
        if request.method not in self.LOGGED_METHODS:
            return response
        
        # Only log if user is authenticated
        if not request.user.is_authenticated:
            return response
        
        # Determine action type from path and method
        action_type = self.determine_action_type(request.path, request.method)
        
        if action_type:
            try:
                SystemLog.objects.create(
                    user=request.user,
                    action_type=action_type,
                    description=f"{request.method} {request.path}",
                    ip_address=request._audit_data.get('ip_address', ''),
                    user_agent=request._audit_data.get('user_agent', ''),
                    details=json.dumps({
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                    })
                )
            except Exception as e:
                # Don't break the request if logging fails
                print(f"Audit logging failed: {e}")
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip[:45]  # IPv6 max length
    
    @staticmethod
    def determine_action_type(path, method):
        """Determine action type from path and method"""
        path_lower = path.lower()
        
        # Map paths to action types
        if '/api/' in path_lower or '/data-management/' in path_lower:
            if method == 'POST':
                if 'user' in path_lower:
                    return 'user_created'
                elif 'topic' in path_lower:
                    return 'topic_created'
                elif 'post' in path_lower:
                    return 'post_created'
                elif 'backup' in path_lower:
                    return 'backup_created'
                elif 'import' in path_lower:
                    return 'data_imported'
                return 'data_created'
            
            elif method in ['PUT', 'PATCH']:
                if 'user' in path_lower:
                    return 'user_updated'
                elif 'topic' in path_lower:
                    return 'topic_updated'
                elif 'post' in path_lower:
                    return 'post_updated'
                return 'data_updated'
            
            elif method == 'DELETE':
                if 'user' in path_lower:
                    return 'user_deleted'
                elif 'topic' in path_lower:
                    return 'topic_deleted'
                elif 'post' in path_lower:
                    return 'post_deleted'
                elif 'backup' in path_lower:
                    return 'backup_deleted'
                return 'data_deleted'
        
        return None
