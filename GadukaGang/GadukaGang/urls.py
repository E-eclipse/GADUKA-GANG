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
from . import api
from . import analytics_views as analytics
from . import data_management_views as data_mgmt
from . import community_views as community
from . import settings_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),

    # Prometheus metrics endpoint
    path('', include('django_prometheus.urls')),
    
    # Custom admin panel (direct URL only)
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    
    
    # Analytics Dashboard
    path('analytics/', analytics.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/api/data/', analytics.analytics_api_data, name='analytics_api_data'),
    path('analytics/export/', analytics.export_analytics_csv, name='export_analytics_csv'),
    
    # Data Management (CSV Import/Export, Backups)
    path('data-management/csv/', data_mgmt.csv_operations_view, name='csv_operations'),
    path('data-management/csv/import/', data_mgmt.handle_csv_import, name='csv_import_handle'),
    path('data-management/csv/export/<str:entity_type>/', data_mgmt.download_csv_export, name='csv_export_download'),
    path('data-management/backups/', data_mgmt.backup_management_view, name='backup_management'),
    path('data-management/backups/create/', data_mgmt.create_backup, name='backup_create'),
    path('data-management/backups/delete/<str:filename>/', data_mgmt.delete_backup, name='backup_delete'),
    path('data-management/backups/download/<str:filename>/', data_mgmt.download_backup, name='backup_download'),
    path('data-management/db/export/', data_mgmt.export_full_database, name='db_export_full'),
    path('data-management/db/import/', data_mgmt.import_full_database, name='db_import_full'),
    
    # Старые пути для обратной совместимости (перенаправляют на allauth)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Политика конфиденциальности
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    
    # Восстановление пароля
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete_view, name='password_reset_complete'),
    
    # allauth URLs (включает login, logout, signup, password reset, email verification, OAuth)
    path('accounts/', include('allauth.urls')),
    
    # REST API URLs
    path('api/v1/', include('GadukaGang.api_urls')),
    
    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/achievements/', views.achievements_view, name='achievements'),
    path('profile/unlock-admin-token/', views.unlock_admin_token, name='unlock_admin_token'),
    path('profile/<int:user_id>/', views.profile_detail_view, name='profile_detail'),
    
    # Настройки пользователя
    path('settings/', settings_views.user_settings, name='user_settings'),
    path('settings/save/', settings_views.save_settings, name='save_settings'),
    path('settings/filters/save/', settings_views.save_filter_preset, name='save_filter_preset'),
    
    # Форум и сообщества
    path('forum/', community.forum_hub, name='forum_hub'),
    path('communities/', community.community_list, name='community_list'),
    path('communities/create/', community.community_create, name='community_create'),
    path('communities/<int:community_id>/', community.community_detail, name='community_detail'),
    path('communities/<int:community_id>/edit/', community.community_edit, name='community_edit'),
    path('communities/<int:community_id>/join/', community.community_join, name='community_join'),
    path('communities/<int:community_id>/members/', community.community_members, name='community_members'),
    path('communities/<int:community_id>/topics/create/', community.community_topic_create, name='community_topic_create'),
    path('communities/invite/<str:token>/', community.community_invite, name='community_invite'),
    path('communities/<int:community_id>/notifications/toggle/', community.toggle_community_notifications, name='toggle_community_notifications'),
    
    # Подписки на пользователей
    path('users/<int:user_id>/follow/', community.follow_user, name='follow_user'),
    path('users/<int:user_id>/followers/', community.followers_list, name='followers_list'),
    path('users/<int:user_id>/following/', community.following_list, name='following_list'),
    path('feed/', community.activity_feed, name='activity_feed'),
    
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
    
    # API Documentation
    path('api/', api.api_documentation, name='api_documentation'),
    
    # CRUD API для всех моделей
    # User API
    path('api/users/', api.user_list_create, name='api_user_list_create'),
    path('api/users/<int:user_id>/', api.user_detail, name='api_user_detail'),
    
    # UserProfile API
    path('api/userprofiles/', api.userprofile_list_create, name='api_userprofile_list_create'),
    path('api/userprofiles/<int:user_id>/', api.userprofile_detail, name='api_userprofile_detail'),
    
    # Section API
    path('api/sections/', api.section_list_create, name='api_section_list_create'),
    path('api/sections/<int:section_id>/', api.section_detail, name='api_section_detail'),
    
    # Topic API
    path('api/topics/', api.topic_list_create, name='api_topic_list_create'),
    path('api/topics/<int:topic_id>/', api.topic_detail, name='api_topic_detail'),
    
    # Post API
    path('api/posts/', api.post_list_create, name='api_post_list_create'),
    path('api/posts/<int:post_id>/', api.post_detail, name='api_post_detail'),
    
    # Achievement API
    path('api/achievements/', api.achievement_list_create, name='api_achievement_list_create'),
    path('api/achievements/<int:achievement_id>/', api.achievement_detail, name='api_achievement_detail'),
    
    # UserAchievement API
    path('api/userachievements/', api.userachievement_list_create, name='api_userachievement_list_create'),
    path('api/userachievements/<int:userachievement_id>/', api.userachievement_detail, name='api_userachievement_detail'),
    
    # UserRank API
    path('api/userranks/', api.userrank_list_create, name='api_userrank_list_create'),
    path('api/userranks/<int:userrank_id>/', api.userrank_detail, name='api_userrank_detail'),
    
    # UserRankProgress API
    path('api/userrankprogresses/', api.userrankprogress_list_create, name='api_userrankprogress_list_create'),
    path('api/userrankprogresses/<int:user_id>/', api.userrankprogress_detail, name='api_userrankprogress_detail'),
    
    # Tag API
    path('api/tags/', api.tag_list_create, name='api_tag_list_create'),
    path('api/tags/<int:tag_id>/', api.tag_detail, name='api_tag_detail'),
    
    # TopicTag API
    path('api/topictags/', api.topictag_list_create, name='api_topictag_list_create'),
    path('api/topictags/<int:topictag_id>/', api.topictag_detail, name='api_topictag_detail'),
    
    # Certificate API
    path('api/certificates/', api.certificate_list_create, name='api_certificate_list_create'),
    path('api/certificates/<int:certificate_id>/', api.certificate_detail, name='api_certificate_detail'),
    
    # UserCertificate API
    path('api/usercertificates/', api.usercertificate_list_create, name='api_usercertificate_list_create'),
    path('api/usercertificates/<int:usercertificate_id>/', api.usercertificate_detail, name='api_usercertificate_detail'),
    
    # Complaint API
    path('api/complaints/', api.complaint_list_create, name='api_complaint_list_create'),
    path('api/complaints/<int:complaint_id>/', api.complaint_detail, name='api_complaint_detail'),
    
    # Chat API
    path('api/chats/', api.chat_list_create, name='api_chat_list_create'),
    path('api/chats/<int:chat_id>/', api.chat_detail, name='api_chat_detail'),
    
    # ChatParticipant API
    path('api/chatparticipants/', api.chatparticipant_list_create, name='api_chatparticipant_list_create'),
    path('api/chatparticipants/<int:chatparticipant_id>/', api.chatparticipant_detail, name='api_chatparticipant_detail'),
    
    # ChatMessage API
    path('api/chatmessages/', api.chatmessage_list_create, name='api_chatmessage_list_create'),
    path('api/chatmessages/<int:chatmessage_id>/', api.chatmessage_detail, name='api_chatmessage_detail'),
    
    # SystemLog API
    path('api/systemlogs/', api.systemlog_list_create, name='api_systemlog_list_create'),
    path('api/systemlogs/<int:systemlog_id>/', api.systemlog_detail, name='api_systemlog_detail'),
    
    # ForumSetting API
    path('api/forumsettings/', api.forumsetting_list_create, name='api_forumsetting_list_create'),
    path('api/forumsettings/<int:forumsetting_id>/', api.forumsetting_detail, name='api_forumsetting_detail'),
    
    # PostLike API
    path('api/postlikes/', api.postlike_list_create, name='api_postlike_list_create'),
    path('api/postlikes/<int:postlike_id>/', api.postlike_detail, name='api_postlike_detail'),
    
    # TopicRating API
    path('api/topicratings/', api.topicrating_list_create, name='api_topicrating_list_create'),
    path('api/topicratings/<int:topicrating_id>/', api.topicrating_detail, name='api_topicrating_detail'),
    
    # UserSubscription API
    path('api/usersubscriptions/', api.usersubscription_list_create, name='api_usersubscription_list_create'),
    path('api/usersubscriptions/<int:usersubscription_id>/', api.usersubscription_detail, name='api_usersubscription_detail'),
    
    # TopicSubscription API
    path('api/topicsubscriptions/', api.topicsubscription_list_create, name='api_topicsubscription_list_create'),
    path('api/topicsubscriptions/<int:topicsubscription_id>/', api.topicsubscription_detail, name='api_topicsubscription_detail'),
    
    # ModeratorAction API
    path('api/moderatoractions/', api.moderatoraction_list_create, name='api_moderatoraction_list_create'),
    path('api/moderatoractions/<int:moderatoraction_id>/', api.moderatoraction_detail, name='api_moderatoraction_detail'),
    
    # AdminLog API
    path('api/adminlogs/', api.adminlog_list_create, name='api_adminlog_list_create'),
    path('api/adminlogs/<int:adminlog_id>/', api.adminlog_detail, name='api_adminlog_detail'),
    
    # Notification API
    path('api/notifications/', api.notification_list_create, name='api_notification_list_create'),
    path('api/notifications/<int:notification_id>/', api.notification_detail, name='api_notification_detail'),
    
    # SearchIndex API
    path('api/searchindices/', api.searchindex_list_create, name='api_searchindex_list_create'),
    path('api/searchindices/<int:searchindex_id>/', api.searchindex_detail, name='api_searchindex_detail'),
    
    # GitHubAuth API
    path('api/githubauths/', api.githubauth_list_create, name='api_githubauth_list_create'),
    path('api/githubauths/<int:user_id>/', api.githubauth_detail, name='api_githubauth_detail'),
    
    # TopicView API
    path('api/topicviews/', api.topicview_list_create, name='api_topicview_list_create'),
    path('api/topicviews/<int:topicview_id>/', api.topicview_detail, name='api_topicview_detail'),
    
    # Теги
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    path('tags/<int:tag_id>/topics/', views.topics_by_tag, name='topics_by_tag'),
    
    # Образование (заменяет практику)
    path('education/', views.practice_view, name='education'),
    
    # Обучение/Образование (курсы)
    path('learning/', views.education_view, name='education_courses'),
    path('learning/course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('learning/lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('learning/lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('learning/run-code/', views.run_python_code, name='run_python_code'),
    
    # Участники форума
    path('members/', views.members_list, name='members_list'),
]

# Кастомный обработчик 404 ошибки
handler404 = views.custom_404_view

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)