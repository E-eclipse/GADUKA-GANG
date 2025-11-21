from rest_framework import serializers
from .models import (
    User, UserProfile, Section, Topic, Post, Achievement, UserAchievement,
    UserRank, UserRankProgress, Tag, TopicTag, Certificate, UserCertificate,
    Complaint, Chat, ChatParticipant, ChatMessage, SystemLog, ForumSetting,
    PostLike, TopicRating, UserSubscription, TopicSubscription, ModeratorAction,
    AdminLog, Notification, SearchIndex, GitHubAuth, TopicView
)


# User Serializers
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                  'registration_date', 'last_login', 'is_active']
        read_only_fields = ['id', 'registration_date']
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'avatar_url', 'bio', 'signature', 'post_count', 
                  'join_date', 'last_activity']
        read_only_fields = ['post_count', 'join_date', 'last_activity']


# Forum Content Serializers
class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model"""
    created_by = UserSerializer(read_only=True)
    topic_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ['id', 'name', 'description', 'created_by', 'created_date', 'topic_count']
        read_only_fields = ['id', 'created_date']
    
    def get_topic_count(self, obj):
        return obj.topic_set.count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']


class TopicTagSerializer(serializers.ModelSerializer):
    """Serializer for TopicTag model"""
    tag = TagSerializer(read_only=True)
    tag_id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tag', write_only=True
    )
    
    class Meta:
        model = TopicTag
        fields = ['id', 'topic', 'tag', 'tag_id']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model"""
    author = UserSerializer(read_only=True)
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source='section', write_only=True
    )
    tags = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'section', 'section_id', 'title', 'author', 'created_date', 
                  'last_post_date', 'is_pinned', 'view_count', 'average_rating', 
                  'rating_count', 'tags', 'post_count']
        read_only_fields = ['id', 'created_date', 'last_post_date', 'view_count', 
                            'average_rating', 'rating_count']
    
    def get_tags(self, obj):
        topic_tags = obj.topic_tags.all()
        return TagSerializer([tt.tag for tt in topic_tags], many=True).data
    
    def get_post_count(self, obj):
        return obj.post_set.count()


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model"""
    author = UserSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), source='topic', write_only=True
    )
    
    class Meta:
        model = Post
        fields = ['id', 'topic', 'topic_id', 'author', 'content', 'created_date', 
                  'last_edited_date', 'edit_count', 'is_deleted', 'like_count', 
                  'dislike_count']
        read_only_fields = ['id', 'created_date', 'last_edited_date', 'edit_count', 
                            'like_count', 'dislike_count']


class PostLikeSerializer(serializers.ModelSerializer):
    """Serializer for PostLike model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PostLike
        fields = ['id', 'post', 'user', 'like_type', 'created_date']
        read_only_fields = ['id', 'created_date']


class TopicRatingSerializer(serializers.ModelSerializer):
    """Serializer for TopicRating model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TopicRating
        fields = ['id', 'topic', 'user', 'rating', 'created_date']
        read_only_fields = ['id', 'created_date']


# Achievement and Certificate Serializers
class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model"""
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'icon_url', 'criteria']


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for UserAchievement model"""
    achievement = AchievementSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    awarded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'earned_date', 'awarded_by']
        read_only_fields = ['id', 'earned_date']


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for Certificate model"""
    class Meta:
        model = Certificate
        fields = ['id', 'name', 'description', 'template_url', 'criteria']


class UserCertificateSerializer(serializers.ModelSerializer):
    """Serializer for UserCertificate model"""
    certificate = CertificateSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    awarded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = UserCertificate
        fields = ['id', 'user', 'certificate', 'awarded_date', 'awarded_by', 
                  'expiration_date']
        read_only_fields = ['id', 'awarded_date']


# Rank Serializers
class UserRankSerializer(serializers.ModelSerializer):
    """Serializer for UserRank model"""
    class Meta:
        model = UserRank
        fields = ['id', 'name', 'required_points', 'icon_url']


class UserRankProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserRankProgress model"""
    rank = UserRankSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserRankProgress
        fields = ['user', 'rank', 'current_points', 'progress_percentage']


# Subscription Serializers
class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model"""
    subscriber = UserSerializer(read_only=True)
    subscribed_to = UserSerializer(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'subscriber', 'subscribed_to', 'created_date']
        read_only_fields = ['id', 'created_date']


class TopicSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for TopicSubscription model"""
    user = UserSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    
    class Meta:
        model = TopicSubscription
        fields = ['id', 'topic', 'user', 'created_date', 'notify_on_new_post']
        read_only_fields = ['id', 'created_date']


# Chat Serializers
class ChatSerializer(serializers.ModelSerializer):
    """Serializer for Chat model"""
    created_by = UserSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['id', 'name', 'chat_type', 'created_by', 'created_date', 
                  'is_active', 'participant_count']
        read_only_fields = ['id', 'created_date']
    
    def get_participant_count(self, obj):
        return obj.chatparticipant_set.filter(left_date__isnull=True).count()


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Serializer for ChatParticipant model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'chat', 'user', 'joined_date', 'left_date', 'role_in_chat']
        read_only_fields = ['id', 'joined_date']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model"""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'chat', 'sender', 'content', 'sent_date', 'is_edited', 
                  'edited_date', 'is_deleted']
        read_only_fields = ['id', 'sent_date', 'is_edited', 'edited_date']


# Moderation Serializers
class ComplaintSerializer(serializers.ModelSerializer):
    """Serializer for Complaint model"""
    reporter = UserSerializer(read_only=True)
    assigned_moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = Complaint
        fields = ['id', 'reporter', 'target_type', 'target_id', 'reason', 
                  'description', 'status', 'assigned_moderator', 'created_date', 
                  'resolved_date']
        read_only_fields = ['id', 'created_date', 'resolved_date']


class ModeratorActionSerializer(serializers.ModelSerializer):
    """Serializer for ModeratorAction model"""
    moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = ModeratorAction
        fields = ['id', 'moderator', 'action_type', 'description', 'target_type', 
                  'target_id', 'created_date']
        read_only_fields = ['id', 'created_date']


class AdminLogSerializer(serializers.ModelSerializer):
    """Serializer for AdminLog model"""
    admin = UserSerializer(read_only=True)
    
    class Meta:
        model = AdminLog
        fields = ['id', 'admin', 'action_type', 'description', 
                  'affected_resource_type', 'affected_resource_id', 'created_date']
        read_only_fields = ['id', 'created_date']


# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'notification_type', 'title', 'message', 'is_read', 
                  'created_date', 'related_resource_type', 'related_resource_id']
        read_only_fields = ['id', 'created_date']


# System Serializers
class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer for SystemLog model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SystemLog
        fields = ['id', 'user', 'action_type', 'action_level', 'description', 
                  'affected_resource_type', 'affected_resource_id', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ForumSettingSerializer(serializers.ModelSerializer):
    """Serializer for ForumSetting model"""
    modified_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ForumSetting
        fields = ['id', 'setting_name', 'setting_value', 'category', 
                  'last_modified', 'modified_by']
        read_only_fields = ['id', 'last_modified']


# TopicView Serializer
class TopicViewSerializer(serializers.ModelSerializer):
    """Serializer for TopicView model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TopicView
        fields = ['id', 'topic', 'user', 'view_date']
        read_only_fields = ['id', 'view_date']
