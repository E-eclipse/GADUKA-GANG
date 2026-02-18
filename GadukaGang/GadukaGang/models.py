from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

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
    karma = models.IntegerField(default=0)  # Added karma field
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
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='topic_tags')
    
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
    verification_code = models.CharField(max_length=64, unique=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = uuid.uuid4().hex
        super().save(*args, **kwargs)

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

# Модель просмотров тем
class TopicView(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    view_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('topic', 'user')
        app_label = 'GadukaGang'# Модель сообществ
class Community(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_communities')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    member_count = models.IntegerField(default=0)
    icon_url = models.URLField(max_length=500, blank=True)
    is_private = models.BooleanField(default=False)
    invite_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_private and not self.invite_token:
            import secrets
            self.invite_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'GadukaGang'
        verbose_name_plural = 'Communities'

# Модель участников сообществ
class CommunityMembership(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('owner', 'Owner'),
    ]
    
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    joined_date = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        unique_together = ('community', 'user')
        app_label = 'GadukaGang'

# Модель связи тем с сообществами
class CommunityTopic(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='community_topics')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='community_topics')
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('community', 'topic')
        app_label = 'GadukaGang'

# Модель подписок на уведомления сообщества
class CommunityNotificationSubscription(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='notification_subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_notification_subscriptions')
    notify_on_new_post = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('community', 'user')
        app_label = 'GadukaGang'

# Модель категории курсов
class CourseCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_it = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        app_label = 'GadukaGang'

# Модель курса обучения
class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending_auto', 'Автопроверка'),
        ('auto_rejected', 'Отклонен автоматически'),
        ('pending_moderation', 'На модерации'),
        ('rejected', 'Отклонен модератором'),
        ('approved', 'Опубликован'),
    ]

    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_courses')
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon_url = models.URLField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    duration_weeks = models.IntegerField(default=0)
    level = models.CharField(max_length=50, default='Начальный')
    has_practice = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    auto_reject_reason = models.TextField(blank=True)
    moderator_comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    payout_method = models.CharField(max_length=30, blank=True)
    payout_details = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        app_label = 'GadukaGang'

# Модель раздела курса
class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        ordering = ['order']
        app_label = 'GadukaGang'

# Модель урока/лекции
class Lesson(models.Model):
    LESSON_TYPES = [
        ('lecture', 'Лекция'),
        ('practice', 'Практическое задание'),
        ('control', 'Контрольная работа'),
    ]
    PRACTICE_MODES = [
        ('code', 'Код'),
        ('quiz', 'Тест'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    section = models.ForeignKey(CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='lecture')
    practice_mode = models.CharField(max_length=20, choices=PRACTICE_MODES, default='code')
    order = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    practice_code_template = models.TextField(blank=True)
    practice_solution = models.TextField(blank=True)
    practice_task = models.TextField(blank=True)
    control_time_limit_minutes = models.PositiveIntegerField(default=30)
    test_cases = models.JSONField(default=list, blank=True)
    control_pass_threshold = models.PositiveIntegerField(default=70)
    control_lock_minutes = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        ordering = ['order']
        app_label = 'GadukaGang'

class CourseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progresses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progresses')
    completed_lessons = models.ManyToManyField(Lesson, blank=True, related_name='completed_by')
    started_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'course')
        app_label = 'GadukaGang'
    
    def get_progress_percentage(self):
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            return 0
        completed_count = self.completed_lessons.count()
        return int((completed_count / total_lessons) * 100)

# Модель доступа к куру (покупка)
class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    is_paid = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')
        app_label = 'GadukaGang'


class CourseFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']
        app_label = 'GadukaGang'


class CourseRating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course', 'user')
        ordering = ['-updated_at']
        app_label = 'GadukaGang'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sold_orders')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    payout_amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    payout_status = models.CharField(max_length=20, default='pending')
    currency = models.CharField(max_length=10, default='RUB')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, default='stub')
    receipt_email = models.EmailField(blank=True)
    billing_name = models.CharField(max_length=200, blank=True)
    billing_phone = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'GadukaGang'


class ControlQuestion(models.Model):
    QUESTION_TYPES = [
        ('single', 'Один вариант'),
        ('multiple', 'Несколько вариантов'),
        ('text', 'Текстовый ответ'),
    ]
    QUESTION_KINDS = [
        ('theory', 'Теоретический'),
        ('practice', 'Практический'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='control_questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    question_kind = models.CharField(max_length=20, choices=QUESTION_KINDS, default='theory')
    prompt = models.TextField()
    practice_input = models.TextField(blank=True)
    practice_output = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    weight = models.PositiveIntegerField(default=1)
    min_words = models.PositiveIntegerField(default=20)
    required_keywords = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.lesson.title} - Q{self.order}"

    class Meta:
        ordering = ['order', 'id']
        app_label = 'GadukaGang'


class ControlQuestionOption(models.Model):
    question = models.ForeignKey(ControlQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"Option {self.order} for Q{self.question_id}"

    class Meta:
        ordering = ['order', 'id']
        app_label = 'GadukaGang'


class ControlAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='control_attempts')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='control_attempts')
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)
    percent = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} / {self.lesson.title} / {self.percent}%"

    class Meta:
        ordering = ['-created_date']
        app_label = 'GadukaGang'


class ControlLock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='control_locks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='control_locks')
    locked_until = models.DateTimeField(null=True, blank=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    last_score = models.PositiveIntegerField(default=0)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        app_label = 'GadukaGang'


class ControlSession(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
    ]
    PHASE_CHOICES = [
        ('initial', 'Initial'),
        ('review', 'Review'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='control_sessions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='control_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='initial')
    question_order = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    skipped = models.JSONField(default=list, blank=True)
    time_limit_seconds = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        app_label = 'GadukaGang'


class CourseModerationLog(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='moderation_logs')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'GadukaGang'


class PayoutTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payout')
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payouts')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payout_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'GadukaGang'


class ContentAttachment(models.Model):
    KIND_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('link', 'Link'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_attachments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='file')
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='attachments/%Y/%m/%d/', blank=True)
    external_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'GadukaGang'





