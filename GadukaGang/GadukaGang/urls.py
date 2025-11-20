"""
URL configuration for GadukaGang project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    
    # Custom admin panel (direct URL only)
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-charts/', views.admin_charts_view, name='admin_charts'),
    
    # Старые пути для обратной совместимости (перенаправляют на allauth)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # allauth URLs (включает login, logout, signup, password reset, email verification, OAuth)
    path('accounts/', include('allauth.urls')),
    
    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/achievements/', views.achievements_view, name='achievements'),
    path('profile/<int:user_id>/', views.profile_detail_view, name='profile_detail'),
    
    # Разделы форума
    path('sections/', views.sections_list, name='sections_list'),
    path('sections/create/', views.section_create, name='section_create'),
    path('sections/<int:section_id>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:section_id>/delete/', views.section_delete, name='section_delete'),
    
    # Темы форума
    path('sections/<int:section_id>/topics/', views.topics_list, name='topics_list'),
    path('sections/<int:section_id>/topics/create/', views.topic_create, name='topic_create'),
    path('topics/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topics/<int:topic_id>/edit/', views.topic_edit, name='topic_edit'),
    path('topics/<int:topic_id>/delete/', views.topic_delete, name='topic_delete'),
    
    # Сообщения
    path('topics/<int:topic_id>/posts/create/', views.post_create, name='post_create'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    
    # API для лайков и оценок
    path('api/posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('api/topics/<int:topic_id>/rating/', views.topic_rating, name='topic_rating'),
    
    # Теги
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    path('tags/<int:tag_id>/topics/', views.topics_by_tag, name='topics_by_tag'),
    
    # Практика
    path('', views.practice_view, name='practice'),
    
    # Участники форума
    path('members/', views.members_list, name='members_list'),
]
# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)