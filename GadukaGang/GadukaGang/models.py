from django.db import models
from django.contrib.auth.models import AbstractUser

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