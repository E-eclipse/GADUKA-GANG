"""
Утилиты для отправки email-уведомлений
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import CommunityNotificationSubscription, CommunityTopic, CommunityMembership


def send_community_topic_notification(community, topic, post):
    """
    Отправляет email-уведомления участникам сообщества о новой теме
    Отправляет всем участникам сообщества, на которые они подписаны
    """
    # Получаем всех участников сообщества
    memberships = CommunityMembership.objects.filter(
        community=community
    ).select_related('user')
    
    # Получаем список пользователей, которые отключили уведомления
    disabled_notifications = set(
        CommunityNotificationSubscription.objects.filter(
            community=community,
            notify_on_new_post=False
        ).values_list('user_id', flat=True)
    )
    
    # Исключаем автора темы и тех, кто отключил уведомления
    recipients = [
        membership.user for membership in memberships
        if membership.user.email 
        and membership.user != post.author
        and membership.user.id not in disabled_notifications
    ]
    
    if not recipients:
        return
    
    # Формируем тему письма
    subject = f'Новая тема в сообществе "{community.name}"'
    
    # Формируем URL темы
    from django.urls import reverse
    try:
        topic_url = settings.SITE_URL.rstrip('/') + reverse('topic_detail', args=[topic.id])
    except:
        topic_url = f"{settings.SITE_URL.rstrip('/')}/topics/{topic.id}/"
    
    # Отправляем письма каждому получателю
    for recipient in recipients:
        try:
            # Формируем текст письма
            message = f"""
Здравствуйте, {recipient.username}!

{"В приватном сообществе" if community.is_private else "В сообществе"} "{community.name}" создана новая тема:

Название: {topic.title}
Автор: {post.author.username}

Ссылка на тему: {topic_url}

---
Это автоматическое уведомление от Gaduka Gang Forum.
"""
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #00ff41, #00cc33); color: #0a0a0a; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #ffffff; padding: 20px; border: 1px solid #e0e0e0; }}
        .topic-info {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #00ff41; border-radius: 3px; }}
        .button {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #00ff41, #00cc33); color: #0a0a0a; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 15px; }}
        .button:hover {{ opacity: 0.9; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #f8f9fa; border-top: 1px solid #e0e0e0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Gaduka Gang Forum</h2>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{recipient.username}</strong>!</p>
            <p>{"В приватном сообществе" if community.is_private else "В сообществе"} <strong>"{community.name}"</strong> создана новая тема:</p>
            <div class="topic-info">
                <p><strong>Название:</strong> {topic.title}</p>
                <p><strong>Автор:</strong> {post.author.username}</p>
            </div>
            <a href="{topic_url}" class="button">Перейти к теме</a>
        </div>
        <div class="footer">
            <p>Это автоматическое уведомление от Gaduka Gang Forum.</p>
            <p>Вы получили это письмо, потому что подписаны на уведомления сообщества "{community.name}".</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Отправляем email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем отправку другим получателям
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка отправки email пользователю {recipient.username}: {str(e)}')


def send_community_post_notification(community, topic, post):
    """
    Отправляет email-уведомления участникам сообщества о новом сообщении в теме
    Отправляет всем участникам сообщества, на которые они подписаны
    """
    # Получаем всех участников сообщества
    memberships = CommunityMembership.objects.filter(
        community=community
    ).select_related('user')
    
    # Получаем список пользователей, которые отключили уведомления
    disabled_notifications = set(
        CommunityNotificationSubscription.objects.filter(
            community=community,
            notify_on_new_post=False
        ).values_list('user_id', flat=True)
    )
    
    # Исключаем автора сообщения и тех, кто отключил уведомления
    recipients = [
        membership.user for membership in memberships
        if membership.user.email 
        and membership.user != post.author
        and membership.user.id not in disabled_notifications
    ]
    
    if not recipients:
        return
    
    # Формируем тему письма
    subject = f'Новое сообщение в теме "{topic.title}"'
    
    # Формируем URL темы
    from django.urls import reverse
    try:
        topic_url = settings.SITE_URL.rstrip('/') + reverse('topic_detail', args=[topic.id])
    except:
        topic_url = f"{settings.SITE_URL.rstrip('/')}/topics/{topic.id}/"
    
    # Отправляем письма каждому получателю
    for recipient in recipients:
        try:
            # Формируем текст письма
            message = f"""
Здравствуйте, {recipient.username}!

В теме "{topic.title}" сообщества "{community.name}" добавлено новое сообщение:

Автор: {post.author.username}
Сообщение: {post.content[:200]}{'...' if len(post.content) > 200 else ''}

Ссылка на тему: {topic_url}

---
Это автоматическое уведомление от Gaduka Gang Forum.
"""
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #00ff41, #00cc33); color: #0a0a0a; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #ffffff; padding: 20px; border: 1px solid #e0e0e0; }}
        .post-info {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #00ff41; border-radius: 3px; }}
        .post-content {{ margin-top: 10px; padding: 12px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 3px; color: #555; }}
        .button {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #00ff41, #00cc33); color: #0a0a0a; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 15px; }}
        .button:hover {{ opacity: 0.9; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background: #f8f9fa; border-top: 1px solid #e0e0e0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Gaduka Gang Forum</h2>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{recipient.username}</strong>!</p>
            <p>В теме <strong>"{topic.title}"</strong> сообщества <strong>"{community.name}"</strong> добавлено новое сообщение:</p>
            <div class="post-info">
                <p><strong>Автор:</strong> {post.author.username}</p>
                <div class="post-content">
                    {post.content[:500]}{'...' if len(post.content) > 500 else ''}
                </div>
            </div>
            <a href="{topic_url}" class="button">Перейти к теме</a>
        </div>
        <div class="footer">
            <p>Это автоматическое уведомление от Gaduka Gang Forum.</p>
            <p>Вы получили это письмо, потому что подписаны на уведомления сообщества "{community.name}".</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Отправляем email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем отправку другим получателям
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка отправки email пользователю {recipient.username}: {str(e)}')

