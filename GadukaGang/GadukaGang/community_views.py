"""
Views для работы с сообществами и страницей форума
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from .models import Community, CommunityMembership, CommunityTopic, Section, Topic, User, UserSubscription, Post
from django.contrib import messages

def forum_hub(request):
    """Главная страница форума с разделами и сообществами"""
    # Официальные разделы
    sections = Section.objects.all().annotate(
        topic_count=Count('topic')
    )[:6]
    
    # Популярные сообщества
    popular_communities = Community.objects.filter(
        is_active=True
    ).order_by('-member_count')[:6]
    
    # Сообщества пользователя (если авторизован)
    user_communities = []
    if request.user.is_authenticated:
        user_communities = Community.objects.filter(
            memberships__user=request.user,
            is_active=True
        ).annotate(
            topic_count=Count('community_topics')
        )[:6]
    
    context = {
        'sections': sections,
        'popular_communities': popular_communities,
        'user_communities': user_communities,
    }
    return render(request, 'forum/forum_hub.html', context)

def community_list(request):
    """Список всех сообществ"""
    search_query = request.GET.get('search', '')
    
    communities = Community.objects.filter(is_active=True).annotate(
        topic_count=Count('community_topics')
    )
    
    if search_query:
        communities = communities.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    communities = communities.order_by('-member_count')
    
    context = {
        'communities': communities,
        'search_query': search_query,
    }
    return render(request, 'forum/community_list.html', context)

def community_detail(request, community_id):
    """Страница отдельного сообщества"""
    community = get_object_or_404(Community, id=community_id, is_active=True)
    
    # Проверка доступа к приватному сообществу
    is_member = False
    user_role = None
    if request.user.is_authenticated:
        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user
        ).first()
        if membership:
            is_member = True
            user_role = membership.role
    
    # Для приватных сообществ показываем страницу, но ограничиваем доступ к контенту
    # Пользователи могут использовать ссылку-приглашение для вступления
    
    # Темы сообщества
    community_topics = CommunityTopic.objects.filter(
        community=community
    ).select_related('topic', 'topic__author').order_by('-created_date')[:20]
    
    # Участники
    members = CommunityMembership.objects.filter(
        community=community
    ).select_related('user').order_by('-joined_date')[:10]
    
    context = {
        'community': community,
        'is_member': is_member,
        'user_role': user_role,
        'community_topics': community_topics,
        'members': members,
    }
    return render(request, 'forum/community_detail.html', context)

@login_required
def community_create(request):
    """Создание нового сообщества"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_private = request.POST.get('is_private') == 'on'
        icon_url = request.POST.get('icon_url', '')
        
        if not name or not description:
            messages.error(request, 'Название и описание обязательны')
            return render(request, 'forum/community_create.html')
        
        # Создание сообщества
        community = Community.objects.create(
            name=name,
            description=description,
            creator=request.user,
            is_private=is_private,
            icon_url=icon_url,
            member_count=1
        )
        
        # Создатель автоматически становится владельцем
        CommunityMembership.objects.create(
            community=community,
            user=request.user,
            role='owner'
        )
        
        messages.success(request, f'Сообщество "{name}" успешно создано!')
        return redirect('community_detail', community_id=community.id)
    
    return render(request, 'forum/community_create.html')

@login_required
def community_edit(request, community_id):
    """Редактирование сообщества"""
    community = get_object_or_404(Community, id=community_id)
    
    # Проверка прав (только владелец или модератор)
    membership = CommunityMembership.objects.filter(
        community=community,
        user=request.user,
        role__in=['owner', 'moderator']
    ).first()
    
    if not membership:
        messages.error(request, 'У вас нет прав для редактирования этого сообщества')
        return redirect('community_detail', community_id=community_id)
    
    if request.method == 'POST':
        community.name = request.POST.get('name', community.name)
        community.description = request.POST.get('description', community.description)
        community.is_private = request.POST.get('is_private') == 'on'
        community.icon_url = request.POST.get('icon_url', community.icon_url)
        community.save()
        
        messages.success(request, 'Сообщество обновлено!')
        return redirect('community_detail', community_id=community_id)
    
    context = {
        'community': community,
    }
    return render(request, 'forum/community_edit.html', context)

@login_required
@require_http_methods(["POST"])
def community_join(request, community_id):
    """Вступление/выход из сообщества"""
    community = get_object_or_404(Community, id=community_id, is_active=True)
    
    membership = CommunityMembership.objects.filter(
        community=community,
        user=request.user
    ).first()
    
    if membership:
        # Выход из сообщества
        if membership.role == 'owner':
            return JsonResponse({
                'success': False,
                'message': 'Владелец не может покинуть сообщество'
            })
        
        membership.delete()
        community.member_count = max(0, community.member_count - 1)
        community.save()
        
        return JsonResponse({
            'success': True,
            'action': 'left',
            'message': 'Вы покинули сообщество',
            'member_count': community.member_count
        })
    else:
        # Вступление в сообщество
        CommunityMembership.objects.create(
            community=community,
            user=request.user,
            role='member'
        )
        community.member_count += 1
        community.save()
        
        return JsonResponse({
            'success': True,
            'action': 'joined',
            'message': 'Вы вступили в сообщество',
            'member_count': community.member_count
        })

def community_members(request, community_id):
    """Список участников сообщества"""
    community = get_object_or_404(Community, id=community_id, is_active=True)
    
    members = CommunityMembership.objects.filter(
        community=community
    ).select_related('user').order_by('-joined_date')
    
    context = {
        'community': community,
        'members': members,
    }
    return render(request, 'forum/community_members.html', context)

@login_required
@require_http_methods(["POST"])
def follow_user(request, user_id):
    """Подписка/отписка от пользователя"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'Нельзя подписаться на самого себя'
        })
    
    subscription = UserSubscription.objects.filter(
        subscriber=request.user,
        subscribed_to=target_user
    ).first()
    
    if subscription:
        # Отписка
        subscription.delete()
        return JsonResponse({
            'success': True,
            'action': 'unfollowed',
            'message': f'Вы отписались от {target_user.username}'
        })
    else:
        # Подписка
        UserSubscription.objects.create(
            subscriber=request.user,
            subscribed_to=target_user
        )
        return JsonResponse({
            'success': True,
            'action': 'followed',
            'message': f'Вы подписались на {target_user.username}'
        })

@login_required
def activity_feed(request):
    """Персонализированная лента активности по подпискам на сообщества"""
    # Получить сообщества, на которые подписан текущий пользователь
    user_communities = CommunityMembership.objects.filter(
        user=request.user
    ).values_list('community_id', flat=True)
    
    # Получить темы из этих сообществ через CommunityTopic
    community_topics = CommunityTopic.objects.filter(
        community_id__in=user_communities
    ).select_related('topic', 'community', 'topic__author', 'topic__section')
    
    # Извлечь сами темы
    feed_topics = [ct.topic for ct in community_topics]
    
    # Применить фильтры
    filter_type = request.GET.get('filter', 'all')
    filter_community = request.GET.get('community', None)
    
    if filter_type == 'recent':
        feed_topics = sorted(feed_topics, key=lambda t: t.created_date, reverse=True)
    elif filter_type == 'popular':
        feed_topics = sorted(feed_topics, key=lambda t: t.view_count, reverse=True)
    elif filter_type == 'rated':
        feed_topics = sorted(feed_topics, key=lambda t: t.average_rating, reverse=True)
    
    if filter_community:
        try:
            community_id = int(filter_community)
            feed_topics = [t for t in feed_topics if any(
                ct.community_id == community_id for ct in community_topics if ct.topic_id == t.id
            )]
        except (ValueError, TypeError):
            pass
    
    # Ограничить количество
    feed_topics = feed_topics[:50]
    
    # Получить список сообществ для фильтра
    user_communities_list = Community.objects.filter(
        id__in=user_communities
    ).order_by('name')
    
    context = {
        'feed_topics': feed_topics,
        'communities_count': len(user_communities),
        'user_communities': user_communities_list,
        'current_filter': filter_type,
        'current_community': filter_community,
    }
    return render(request, 'forum/activity_feed.html', context)

def followers_list(request, user_id):
    """Список подписчиков пользователя"""
    target_user = get_object_or_404(User, id=user_id)
    
    followers = UserSubscription.objects.filter(
        subscribed_to=target_user
    ).select_related('subscriber').order_by('-created_date')
    
    context = {
        'target_user': target_user,
        'followers': followers,
    }
    return render(request, 'forum/followers_list.html', context)

def following_list(request, user_id):
    """Список подписок пользователя"""
    target_user = get_object_or_404(User, id=user_id)
    
    following = UserSubscription.objects.filter(
        subscriber=target_user
    ).select_related('subscribed_to').order_by('-created_date')
    
    context = {
        'target_user': target_user,
        'following': following,
    }
    return render(request, 'forum/following_list.html', context)

@login_required
def community_topic_create(request, community_id):
    """Создание темы в сообществе"""
    community = get_object_or_404(Community, id=community_id, is_active=True)
    
    # Проверка членства
    is_member = CommunityMembership.objects.filter(
        community=community,
        user=request.user
    ).exists()
    
    if not is_member:
        messages.error(request, 'Только участники могут создавать темы в этом сообществе')
        return redirect('community_detail', community_id=community_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if not title or not content:
            messages.error(request, 'Название и содержание обязательны')
            return render(request, 'forum/community_topic_create.html', {'community': community})
        
        # Создаем или получаем специальный раздел для тем сообществ
        section, created = Section.objects.get_or_create(
            name='Сообщества',
            defaults={'description': 'Темы из сообществ'}
        )
        
        topic = Topic.objects.create(
            section=section,
            title=title,
            author=request.user
        )
        
        # Создаем первый пост
        post = Post.objects.create(
            topic=topic,
            author=request.user,
            content=content
        )
        
        # Связываем тему с сообществом
        CommunityTopic.objects.create(
            community=community,
            topic=topic
        )
        
        # Отправляем email-уведомления участникам сообщества
        try:
            from .email_notifications import send_community_topic_notification
            send_community_topic_notification(community, topic, post)
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка отправки email-уведомлений: {str(e)}')
        
        messages.success(request, 'Тема успешно создана!')
        return redirect('topic_detail', topic_id=topic.id)
    
    return render(request, 'forum/community_topic_create.html', {'community': community})

def community_invite(request, token):
    """Присоединение к приватному сообществу по ссылке-приглашению"""
    community = get_object_or_404(Community, invite_token=token, is_private=True, is_active=True)
    
    if not request.user.is_authenticated:
        messages.info(request, 'Войдите, чтобы присоединиться к сообществу')
        return redirect('account_login')
    
    # Проверяем, не является ли пользователь уже участником
    membership = CommunityMembership.objects.filter(
        community=community,
        user=request.user
    ).first()
    
    if membership:
        messages.info(request, 'Вы уже являетесь участником этого сообщества')
        return redirect('community_detail', community_id=community.id)
    
    # Добавляем пользователя в сообщество
    CommunityMembership.objects.create(
        community=community,
        user=request.user,
        role='member'
    )
    community.member_count += 1
    community.save()
    
    messages.success(request, f'Вы успешно присоединились к сообществу "{community.name}"!')
    return redirect('community_detail', community_id=community.id)

@login_required
@require_http_methods(["POST"])
def toggle_community_notifications(request, community_id):
    """Переключение email-уведомлений для сообщества"""
    from .models import CommunityNotificationSubscription
    
    community = get_object_or_404(Community, id=community_id, is_active=True)
    
    # Проверяем членство
    is_member = CommunityMembership.objects.filter(
        community=community,
        user=request.user
    ).exists()
    
    if not is_member:
        return JsonResponse({
            'success': False,
            'message': 'Вы не являетесь участником этого сообщества'
        })
    
    # Переключаем подписку
    # По умолчанию все участники получают уведомления
    # Для отключения создаем запись с notify_on_new_post=False
    subscription = CommunityNotificationSubscription.objects.filter(
        community=community,
        user=request.user
    ).first()
    
    if subscription:
        # Если есть запись с notify_on_new_post=False - удаляем её (включаем уведомления)
        if not subscription.notify_on_new_post:
            subscription.delete()
            return JsonResponse({
                'success': True,
                'subscribed': True,
                'message': 'Уведомления включены'
            })
        else:
            # Если есть запись с notify_on_new_post=True - меняем на False (отключаем)
            subscription.notify_on_new_post = False
            subscription.save()
            return JsonResponse({
                'success': True,
                'subscribed': False,
                'message': 'Уведомления отключены'
            })
    else:
        # Нет записи - значит уведомления включены по умолчанию
        # Создаем запись с notify_on_new_post=False для отключения
        CommunityNotificationSubscription.objects.create(
            community=community,
            user=request.user,
            notify_on_new_post=False
        )
        return JsonResponse({
            'success': True,
            'subscribed': False,
            'message': 'Уведомления отключены'
        })

