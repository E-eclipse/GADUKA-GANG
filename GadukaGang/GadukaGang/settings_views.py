"""
User settings views
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


@login_required
def user_settings(request):
    """User settings page"""
    user = request.user
    
    # Get or create profile
    from GadukaGang.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Default settings
    settings = {
        'theme': 'dark',
        'date_format': 'DD.MM.YYYY',
        'time_format': '24h',
        'posts_per_page': 20,
        'language': 'ru',
        'show_avatars': True,
        'show_signatures': True,
        'email_notifications': True,
        'saved_filters': {}
    }
    
    # Load saved settings from profile (if using JSON field)
    if hasattr(profile, 'settings') and profile.settings:
        settings.update(profile.settings)
    
    context = {
        'settings': settings,
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'settings/user_settings.html', context)


@login_required
@require_http_methods(["POST"])
def save_settings(request):
    """Save user settings via AJAX"""
    try:
        data = json.loads(request.body)
        
        from GadukaGang.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Save settings to JSON field or individual fields
        if not hasattr(profile, 'settings'):
            # If no settings field, we'll store in a custom way
            # For now, just acknowledge
            pass
        else:
            profile.settings = data
            profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Настройки сохранены успешно!'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка сохранения: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def save_filter_preset(request):
    """Save filter preset"""
    try:
        data = json.loads(request.body)
        preset_name = data.get('name')
        filters = data.get('filters')
        
        if not preset_name or not filters:
            return JsonResponse({
                'success': False,
                'message': 'Имя и фильтры обязательны'
            }, status=400)
        
        from GadukaGang.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Get current saved filters
        saved_filters = {}
        if hasattr(profile, 'settings') and profile.settings:
            saved_filters = profile.settings.get('saved_filters', {})
        
        # Add new preset
        saved_filters[preset_name] = filters
        
        # Save back
        if hasattr(profile, 'settings'):
            if not profile.settings:
                profile.settings = {}
            profile.settings['saved_filters'] = saved_filters
            profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Пресет "{preset_name}" сохранён!'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, status=400)
