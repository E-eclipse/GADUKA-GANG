from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# Модель пользователя
class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin_level_1', 'Admin Level 1'),
        ('admin_level_2', 'Admin Level 2'),
        ('admin_level_3', 'Admin Level 3'),
        ('super_admin', 'Super Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'GadukaGang'

# Модель профиля пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    bio = models.TextField(blank=True)
    signature = models.TextField(blank=True)
    post_count = models.IntegerField(default=0)
    join_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'GadukaGang'

# Модель разделов форума
class Section(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'GadukaGang'

# Модель тем форума
class Topic(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    last_post_date = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

    class Meta:
        app_label = 'GadukaGang'

# Модель сообщений
class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    last_edited_date = models.DateTimeField(null=True, blank=True)
    edit_count = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Post by {self.author.username} in {self.topic.title}"

    class Meta:
        app_label = 'GadukaGang'

# Модель достижений
class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(max_length=500, blank=True)
    criteria = models.JSONField()
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'GadukaGang'

# Модель достижений пользователей
class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awarded_achievements')
    
    class Meta:
        unique_together = ('user', 'achievement')
        app_label = 'GadukaGang'

# Модель рангов пользователей
class UserRank(models.Model):
    name = models.CharField(max_length=50)
    required_points = models.IntegerField()
    icon_url = models.URLField(max_length=500, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'GadukaGang'

# Модель прогресса рангов пользователей
class UserRankProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    rank = models.ForeignKey(UserRank, on_delete=models.SET_NULL, null=True)
    current_points = models.IntegerField(default=0)
    progress_percentage = models.IntegerField(default=0)

    class Meta:
        app_label = 'GadukaGang'

# Модель тегов
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#000000')
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'GadukaGang'

# Модель связи тегов с темами
class TopicTag(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('topic', 'tag')
        app_label = 'GadukaGang'

# Модель сертификатов
class Certificate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    template_url = models.URLField(max_length=500, blank=True)
    criteria = models.JSONField()
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'GadukaGang'

# Модель сертификатов пользователей
class UserCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_certificates')
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE)
    awarded_date = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awarded_certificates')
    expiration_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'GadukaGang'

# Модель жалоб
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('post', 'Post'),
        ('topic', 'Topic'),
        ('user', 'User'),
        ('chat_message', 'Chat Message'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_complaints')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.IntegerField()
    reason = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_complaints')
    created_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'GadukaGang'

# Модель чатов
class Chat(models.Model):
    CHAT_TYPE_CHOICES = [
        ('private', 'Private'),
        ('group', 'Group'),
        ('support', 'Support'),
    ]
    
    name = models.CharField(max_length=100, blank=True)
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPE_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name or f"Chat {self.id}"

    class Meta:
        app_label = 'GadukaGang'

# Модель участников чатов
class ChatParticipant(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_date = models.DateTimeField(auto_now_add=True)
    left_date = models.DateTimeField(null=True, blank=True)
    role_in_chat = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        unique_together = ('chat', 'user')
        app_label = 'GadukaGang'

# Модель сообщений в чатах
class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_date = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        app_label = 'GadukaGang'

# Модель системных логов
class SystemLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50)
    action_level = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    description = models.TextField()
    affected_resource_type = models.CharField(max_length=50, blank=True)
    affected_resource_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'GadukaGang'

# Модель настроек форума
class ForumSetting(models.Model):
    setting_name = models.CharField(max_length=100, unique=True)
    setting_value = models.JSONField()
    category = models.CharField(max_length=50)
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.setting_name

    class Meta:
        app_label = 'GadukaGang'

# Модель лайков/дизлайков сообщений
class PostLike(models.Model):
    LIKE_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    like_type = models.CharField(max_length=10, choices=LIKE_CHOICES)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
        app_label = 'GadukaGang'

# Модель оценок тем
class TopicRating(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('topic', 'user')
        app_label = 'GadukaGang'

# Модель подписок на пользователей
class UserSubscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('subscriber', 'subscribed_to')
        app_label = 'GadukaGang'
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.subscriber == self.subscribed_to:
            raise ValidationError('Пользователь не может подписаться сам на себя.')

# Модель подписок на темы
class TopicSubscription(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='subscribers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_subscriptions')
    created_date = models.DateTimeField(auto_now_add=True)
    notify_on_new_post = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('topic', 'user')
        app_label = 'GadukaGang'

# Модель логов действий модераторов
class ModeratorAction(models.Model):
    ACTION_TYPES = [
        ('delete_post', 'Delete Post'),
        ('delete_topic', 'Delete Topic'),
        ('edit_post', 'Edit Post'),
        ('edit_topic', 'Edit Topic'),
        ('pin_topic', 'Pin Topic'),
        ('unpin_topic', 'Unpin Topic'),
        ('block_user', 'Block User'),
        ('unblock_user', 'Unblock User'),
        ('award_achievement', 'Award Achievement'),
        ('award_rank', 'Award Rank'),
        ('process_complaint', 'Process Complaint'),
    ]
    
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='moderator_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    target_type = models.CharField(max_length=50)  # 'post', 'topic', 'user', etc.
    target_id = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'GadukaGang'

# Модель логов действий администраторов
class AdminLog(models.Model):
    ACTION_TYPES = [
        ('assign_moderator', 'Assign Moderator'),
        ('remove_moderator', 'Remove Moderator'),
        ('change_user_role', 'Change User Role'),
        ('create_section', 'Create Section'),
        ('delete_section', 'Delete Section'),
        ('update_settings', 'Update Settings'),
        ('create_backup', 'Create Backup'),
        ('restore_backup', 'Restore Backup'),
        ('system_update', 'System Update'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    affected_resource_type = models.CharField(max_length=50, blank=True)
    affected_resource_id = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'GadukaGang'

# Модель уведомлений пользователей
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_post_in_topic', 'New Post in Topic'),
        ('reply_to_post', 'Reply to Post'),
        ('post_liked', 'Post Liked'),
        ('post_disliked', 'Post Disliked'),
        ('achievement_earned', 'Achievement Earned'),
        ('complaint_resolved', 'Complaint Resolved'),
        ('chat_message', 'Chat Message'),
        ('user_subscribed', 'User Subscribed'),
        ('topic_subscribed', 'Topic Subscribed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    related_resource_type = models.CharField(max_length=50, blank=True)
    related_resource_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
        app_label = 'GadukaGang'

# Модель индекса для поиска (опционально)
class SearchIndex(models.Model):
    content_type = models.CharField(max_length=50)  # 'topic', 'post'
    object_id = models.IntegerField()
    search_vector = models.TextField()  # Полнотекстовый вектор для поиска
    tags = models.TextField(blank=True)  # Теги через запятую
    author_username = models.CharField(max_length=150, blank=True)
    created_date = models.DateTimeField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        app_label = 'GadukaGang'

# Модель GitHub OAuth данных (опционально)
class GitHubAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='github_auth')
    github_id = models.CharField(max_length=100, unique=True)
    github_username = models.CharField(max_length=150)
    access_token = models.CharField(max_length=500)  # В production - зашифровать
    refresh_token = models.CharField(max_length=500, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'GadukaGang'