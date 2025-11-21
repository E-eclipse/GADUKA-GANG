from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone

from .models import (
    User, UserProfile, Section, Topic, Post, Achievement, UserAchievement,
    UserRank, UserRankProgress, Tag, TopicTag, Certificate, UserCertificate,
    Complaint, Chat, ChatParticipant, ChatMessage, PostLike, TopicRating,
    UserSubscription, TopicSubscription, Notification, TopicView
)
from .serializers import (
    UserSerializer, UserProfileSerializer, SectionSerializer, TopicSerializer,
    PostSerializer, AchievementSerializer, UserAchievementSerializer,
    UserRankSerializer, UserRankProgressSerializer, TagSerializer,
    TopicTagSerializer, CertificateSerializer, UserCertificateSerializer,
    ComplaintSerializer, ChatSerializer, ChatParticipantSerializer,
    ChatMessageSerializer, PostLikeSerializer, TopicRatingSerializer,
    UserSubscriptionSerializer, TopicSubscriptionSerializer,
    NotificationSerializer, TopicViewSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly, IsModeratorOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['registration_date', 'username']
    ordering = ['-registration_date']
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get user profile"""
        user = self.get_object()
        try:
            profile = user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get user statistics"""
        user = self.get_object()
        stats = {
            'total_posts': Post.objects.filter(author=user, is_deleted=False).count(),
            'total_topics': Topic.objects.filter(author=user).count(),
            'total_likes_received': PostLike.objects.filter(post__author=user, like_type='like').count(),
            'achievements_count': UserAchievement.objects.filter(user=user).count(),
            'certificates_count': UserCertificate.objects.filter(user=user).count(),
        }
        return Response(stats)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile model.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Section model.
    Only admins can create/update/delete sections.
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_date', 'name']
    ordering = ['name']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Get all topics in this section"""
        section = self.get_object()
        topics = Topic.objects.filter(section=section)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_date')
        topics = topics.order_by(ordering)
        
        page = self.paginate_queryset(topics)
        if page is not None:
            serializer = TopicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Topic model.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['section', 'author', 'is_pinned']
    search_fields = ['title']
    ordering_fields = ['created_date', 'last_post_date', 'view_count', 'average_rating']
    ordering = ['-last_post_date']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # Record view if user is authenticated
        if request.user.is_authenticated:
            TopicView.objects.update_or_create(
                topic=instance,
                user=request.user
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get all posts in this topic"""
        topic = self.get_object()
        posts = Post.objects.filter(topic=topic, is_deleted=False)
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsModeratorOrReadOnly])
    def pin(self, request, pk=None):
        """Pin/unpin a topic"""
        topic = self.get_object()
        topic.is_pinned = not topic.is_pinned
        topic.save(update_fields=['is_pinned'])
        return Response({'is_pinned': topic.is_pinned})
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending topics (most views in last 7 days)"""
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        topics = Topic.objects.filter(
            created_date__gte=week_ago
        ).annotate(
            recent_posts=Count('post', filter=Q(post__created_date__gte=week_ago))
        ).order_by('-recent_posts', '-view_count')[:10]
        
        serializer = self.get_serializer(topics, many=True)
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post model.
    """
    queryset = Post.objects.filter(is_deleted=False)
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['topic', 'author']
    search_fields = ['content']
    ordering_fields = ['created_date', 'like_count']
    ordering = ['created_date']
    
    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        
        # Update topic's last_post_date
        post.topic.last_post_date = timezone.now()
        post.topic.save(update_fields=['last_post_date'])
        
        # Update user's post count
        try:
            profile = self.request.user.userprofile
            profile.post_count += 1
            profile.save(update_fields=['post_count'])
        except UserProfile.DoesNotExist:
            pass
    
    def perform_update(self, serializer):
        post = serializer.save(
            last_edited_date=timezone.now(),
            edit_count=serializer.instance.edit_count + 1
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like or dislike a post"""
        post = self.get_object()
        like_type = request.data.get('like_type', 'like')
        
        if like_type not in ['like', 'dislike']:
            return Response({'error': 'Invalid like_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already liked/disliked
        existing_like = PostLike.objects.filter(post=post, user=request.user).first()
        
        if existing_like:
            if existing_like.like_type == like_type:
                # Remove like/dislike
                existing_like.delete()
                if like_type == 'like':
                    post.like_count = max(0, post.like_count - 1)
                else:
                    post.dislike_count = max(0, post.dislike_count - 1)
                post.save()
                return Response({'status': 'removed', 'like_count': post.like_count, 'dislike_count': post.dislike_count})
            else:
                # Change like to dislike or vice versa
                if existing_like.like_type == 'like':
                    post.like_count = max(0, post.like_count - 1)
                    post.dislike_count += 1
                else:
                    post.dislike_count = max(0, post.dislike_count - 1)
                    post.like_count += 1
                
                existing_like.like_type = like_type
                existing_like.save()
                post.save()
                return Response({'status': 'changed', 'like_count': post.like_count, 'dislike_count': post.dislike_count})
        else:
            # Create new like/dislike
            PostLike.objects.create(post=post, user=request.user, like_type=like_type)
            if like_type == 'like':
                post.like_count += 1
            else:
                post.dislike_count += 1
            post.save()
            return Response({'status': 'added', 'like_count': post.like_count, 'dislike_count': post.dislike_count})


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tag model.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Get all topics with this tag"""
        tag = self.get_object()
        topic_tags = TopicTag.objects.filter(tag=tag)
        topics = [tt.topic for tt in topic_tags]
        
        page = self.paginate_queryset(topics)
        if page is not None:
            serializer = TopicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


class TopicRatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TopicRating model.
    """
    queryset = TopicRating.objects.all()
    serializer_class = TopicRatingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['topic', 'user']
    
    def perform_create(self, serializer):
        rating = serializer.save(user=self.request.user)
        
        # Update topic's average rating
        topic = rating.topic
        ratings = TopicRating.objects.filter(topic=topic)
        topic.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        topic.rating_count = ratings.count()
        topic.save(update_fields=['average_rating', 'rating_count'])


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Achievement model (read-only for regular users).
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [AllowAny]


class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for UserAchievement model (read-only).
    """
    queryset = UserAchievement.objects.all()
    serializer_class = UserAchievementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'achievement']


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Certificate model (read-only for regular users).
    """
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [AllowAny]


class UserCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for UserCertificate model (read-only).
    """
    queryset = UserCertificate.objects.all()
    serializer_class = UserCertificateSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'certificate']


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification model.
    Users can only see their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Chat model.
    """
    queryset = Chat.objects.filter(is_active=True)
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see chats they're part of
        return Chat.objects.filter(
            chatparticipant__user=self.request.user,
            chatparticipant__left_date__isnull=True,
            is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ChatMessage model.
    """
    queryset = ChatMessage.objects.filter(is_deleted=False)
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['chat']
    ordering = ['sent_date']
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class ComplaintViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Complaint model.
    """
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'target_type']
    
    def get_queryset(self):
        # Moderators and admins see all complaints, users see only their own
        if self.request.user.role in ['moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']:
            return Complaint.objects.all()
        return Complaint.objects.filter(reporter=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
