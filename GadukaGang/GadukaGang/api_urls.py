from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .api_views import (
    UserViewSet, UserProfileViewSet, SectionViewSet, TopicViewSet,
    PostViewSet, TagViewSet, TopicRatingViewSet, AchievementViewSet,
    UserAchievementViewSet, CertificateViewSet, UserCertificateViewSet,
    NotificationViewSet, ChatViewSet, ChatMessageViewSet, ComplaintViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ratings', TopicRatingViewSet, basename='topicrating')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-achievements', UserAchievementViewSet, basename='userachievement')
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'user-certificates', UserCertificateViewSet, basename='usercertificate')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'chat-messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'complaints', ComplaintViewSet, basename='complaint')

# Schema view for API documentation (Swagger/OpenAPI)
schema_view = get_schema_view(
    openapi.Info(
        title="Gaduka Gang Forum API",
        default_version='v1',
        description="REST API for Gaduka Gang Forum",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@gadukagang.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# API URL patterns
urlpatterns = [
    # API root
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', obtain_auth_token, name='api-login'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # API Documentation (Swagger)
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='api-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='api-swagger-json'),
]
