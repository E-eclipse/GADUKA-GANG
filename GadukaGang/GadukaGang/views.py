from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
import markdown
from .forms import CustomUserCreationForm, SectionForm, TopicForm, PostForm
from .models import (
    User, UserProfile, Section, Topic, Post, Tag, TopicTag, 
    Certificate, UserCertificate, Achievement, UserAchievement,
    UserRank, UserRankProgress, PostLike, TopicRating
)
from django.urls import reverse
from .decorators import admin_required

User = get_user_model()

def index(request):
    """
    View function for the home page of Gaduka Gang forum
    """
    # Получаем статистику для главной страницы
    stats = {
        'total_users': User.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_posts': Post.objects.count(),
        'online_users': 0,  # Нужно будет реализовать отслеживание онлайн-пользователей
    }
    
    # Получаем последние темы с тегами
    latest_topics = Topic.objects.select_related('section', 'author').prefetch_related('topic_tags__tag').order_by('-created_date')[:5]
    
    # Получаем активных пользователей
    active_users = User.objects.order_by('-last_login')[:10]
    
    # Получаем популярные теги
    popular_tags = Tag.objects.annotate(
        topics_count=Count('topic_tags')
    ).order_by('-topics_count')[:10]
    
    context = {
        'stats': stats,
        'latest_topics': latest_topics,
        'active_users': active_users,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'index.html', context)

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    View function for handling user login
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page or the page the user was trying to access
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    View function for handling user logout
    """
    logout(request)
    return redirect('home')

def register_view(request):
    """
    View function for handling user registration
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)
            # Автоматически логиним пользователя после регистрации
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request):
    """Просмотр профиля пользователя"""
    # Получаем или создаем профиль пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Получаем сертификаты пользователя
    user_certificates = UserCertificate.objects.filter(user=request.user).select_related('certificate')
    
    # Обновляем количество сообщений пользователя
    post_count = Post.objects.filter(author=request.user, is_deleted=False).count()
    user_profile.post_count = post_count
    user_profile.save(update_fields=['post_count'])
    
    context = {
        'user_profile': user_profile,
        'user_certificates': user_certificates,
    }
    return render(request, 'profile.html', context)


def profile_detail_view(request, user_id):
    """Просмотр профиля другого пользователя"""
    user = get_object_or_404(User, id=user_id)
    
    # Получаем или создаем профиль пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Получаем сертификаты пользователя
    user_certificates = UserCertificate.objects.filter(user=user).select_related('certificate')
    
    # Получаем достижения пользователя с информацией о редкости
    from django.db.models import Count
    user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    
    # Получаем общее количество пользователей для расчета редкости
    total_users = User.objects.filter(is_active=True).count()
    
    # Добавляем информацию о редкости для каждого достижения пользователя
    achievements_with_rarity = []
    for user_achievement in user_achievements:
        # Считаем, сколько пользователей получило это достижение
        achievement_recipients = UserAchievement.objects.filter(
            achievement=user_achievement.achievement
        ).count()
        
        # Рассчитываем процент получивших достижение
        if total_users > 0:
            rarity_percentage = (achievement_recipients / total_users) * 100
        else:
            rarity_percentage = 0
            
        achievements_with_rarity.append({
            'user_achievement': user_achievement,
            'recipients_count': achievement_recipients,
            'rarity_percentage': rarity_percentage,
            'is_rare': rarity_percentage < 10  # Редкое достижение, если менее 10% пользователей получили его
        })
    
    # Сортируем по редкости (сначала редкие)
    achievements_with_rarity.sort(key=lambda x: x['rarity_percentage'])
    
    # Обновляем количество сообщений пользователя
    post_count = Post.objects.filter(author=user, is_deleted=False).count()
    user_profile.post_count = post_count
    user_profile.save(update_fields=['post_count'])
    
    context = {
        'user_profile': user_profile,
        'user_certificates': user_certificates,
        'user_achievements_with_rarity': achievements_with_rarity,
        'viewed_user': user,
    }
    return render(request, 'profile_detail.html', context)

@login_required
def edit_profile_view(request):
    """
    View function for editing user profile
    """
    if request.method == 'POST':
        # Get the user profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Update profile fields
        user_profile.bio = request.POST.get('bio', user_profile.bio)
        user_profile.signature = request.POST.get('signature', user_profile.signature)
        
        # Update user fields
        request.user.email = request.POST.get('email', request.user.email)
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        
        # Save both user and profile
        request.user.save()
        user_profile.save()
        
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')
    
    # For GET request, show the edit form
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user_profile': user_profile,
    }
    
    return render(request, 'edit_profile.html', context)

@admin_required
def admin_panel_view(request):
    """
    Custom admin panel (placeholder dashboard).
    Accessible only by admins via direct URL.
    Provides links to Django admin for managing all tables.
    """
    admin_links = [
        { 'name': 'Пользователи', 'url': reverse('admin:GadukaGang_user_changelist') },
        { 'name': 'Профили пользователей', 'url': reverse('admin:GadukaGang_userprofile_changelist') },
        { 'name': 'Разделы', 'url': reverse('admin:GadukaGang_section_changelist') },
        { 'name': 'Темы', 'url': reverse('admin:GadukaGang_topic_changelist') },
        { 'name': 'Сообщения', 'url': reverse('admin:GadukaGang_post_changelist') },
        { 'name': 'Достижения', 'url': reverse('admin:GadukaGang_achievement_changelist') },
        { 'name': 'Достижения пользователей', 'url': reverse('admin:GadukaGang_userachievement_changelist') },
        { 'name': 'Ранги', 'url': reverse('admin:GadukaGang_userrank_changelist') },
        { 'name': 'Прогресс рангов', 'url': reverse('admin:GadukaGang_userrankprogress_changelist') },
        { 'name': 'Теги', 'url': reverse('admin:GadukaGang_tag_changelist') },
        { 'name': 'Теги тем', 'url': reverse('admin:GadukaGang_topictag_changelist') },
        { 'name': 'Сертификаты', 'url': reverse('admin:GadukaGang_certificate_changelist') },
        { 'name': 'Сертификаты пользователей', 'url': reverse('admin:GadukaGang_usercertificate_changelist') },
        { 'name': 'Жалобы', 'url': reverse('admin:GadukaGang_complaint_changelist') },
        { 'name': 'Чаты', 'url': reverse('admin:GadukaGang_chat_changelist') },
        { 'name': 'Участники чатов', 'url': reverse('admin:GadukaGang_chatparticipant_changelist') },
        { 'name': 'Сообщения чатов', 'url': reverse('admin:GadukaGang_chatmessage_changelist') },
        { 'name': 'Системные логи', 'url': reverse('admin:GadukaGang_systemlog_changelist') },
        { 'name': 'Настройки форума', 'url': reverse('admin:GadukaGang_forumsetting_changelist') },
        { 'name': 'Лайки сообщений', 'url': reverse('admin:GadukaGang_postlike_changelist') },
        { 'name': 'Оценки тем', 'url': reverse('admin:GadukaGang_topicrating_changelist') },
        { 'name': 'Подписки на пользователей', 'url': reverse('admin:GadukaGang_usersubscription_changelist') },
        { 'name': 'Подписки на темы', 'url': reverse('admin:GadukaGang_topicsubscription_changelist') },
        { 'name': 'Действия модераторов', 'url': reverse('admin:GadukaGang_moderatoraction_changelist') },
        { 'name': 'Логи администраторов', 'url': reverse('admin:GadukaGang_adminlog_changelist') },
        { 'name': 'Уведомления', 'url': reverse('admin:GadukaGang_notification_changelist') },
        { 'name': 'Поисковый индекс', 'url': reverse('admin:GadukaGang_searchindex_changelist') },
        { 'name': 'GitHub OAuth', 'url': reverse('admin:GadukaGang_githubauth_changelist') },
    ]

    context = {
        'admin_links': admin_links,
    }
    return render(request, 'admin_panel.html', context)

@admin_required
def admin_charts_view(request):
    """
    Admin charts page with beautiful visualizations.
    """
    # Get statistics for charts
    stats = {
        'total_users': User.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_sections': Section.objects.count(),
        'total_posts': Post.objects.count(),
        'total_complaints': 0,  # We'll calculate this properly
    }
    
    context = {
        'stats': stats,
    }
    return render(request, 'admin_charts.html', context)

# ========== РАЗДЕЛЫ (SECTIONS) ==========

def sections_list(request):
    """Список всех разделов форума"""
    sections = Section.objects.annotate(
        topics_count=Count('topic')
    ).order_by('name')
    
    context = {
        'sections': sections,
    }
    return render(request, 'forum/sections_list.html', context)

@admin_required
def section_create(request):
    """Создание нового раздела (только для админов)"""
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.created_by = request.user
            section.save()
            messages.success(request, 'Раздел успешно создан!')
            return redirect('sections_list')
    else:
        form = SectionForm()
    
    return render(request, 'forum/section_form.html', {'form': form, 'action': 'Создать'})

@admin_required
def section_edit(request, section_id):
    """Редактирование раздела (только для админов)"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Раздел успешно обновлен!')
            return redirect('sections_list')
    else:
        form = SectionForm(instance=section)
    
    return render(request, 'forum/section_form.html', {'form': form, 'section': section, 'action': 'Редактировать'})

@admin_required
@require_POST
def section_delete(request, section_id):
    """Удаление раздела (только для админов)"""
    section = get_object_or_404(Section, id=section_id)
    section.delete()
    messages.success(request, 'Раздел успешно удален!')
    return redirect('sections_list')

# ========== ТЕМЫ (TOPICS) ==========

def topics_list(request, section_id):
    """Список тем в разделе с пагинацией и сортировкой"""
    section = get_object_or_404(Section, id=section_id)
    
    # Параметры сортировки
    sort_by = request.GET.get('sort', 'date')  # date, popularity, rating
    order = request.GET.get('order', 'desc')  # asc, desc
    
    # Получаем темы с аннотациями
    topics = Topic.objects.filter(section=section).select_related('author').prefetch_related('topic_tags__tag').annotate(
        posts_count=Count('post'),
        ratings_avg=Avg('ratings__rating')
    )
    
    # Сортировка
    if sort_by == 'date':
        topics = topics.order_by('-created_date' if order == 'desc' else 'created_date')
    elif sort_by == 'popularity':
        topics = topics.order_by('-view_count' if order == 'desc' else 'view_count')
    elif sort_by == 'rating':
        topics = topics.order_by('-average_rating' if order == 'desc' else 'average_rating')
    
    # Пагинация
    paginator = Paginator(topics, 20)  # 20 тем на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'section': section,
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': order,
    }
    return render(request, 'forum/topics_list.html', context)

@login_required
def topic_create(request, section_id):
    """Создание новой темы"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.section = section
            topic.author = request.user
            topic.save()
            
            # Сохраняем теги
            tags = form.cleaned_data.get('tags', [])
            for tag in tags:
                TopicTag.objects.create(topic=topic, tag=tag)
            
            # Создаем первое сообщение в теме
            post_content = request.POST.get('post_content', '')
            if post_content:
                Post.objects.create(
                    topic=topic,
                    author=request.user,
                    content=post_content
                )
            
            # Проверяем достижения после создания темы
            from .signals import check_topic_achievements
            check_topic_achievements(request.user)
            
            messages.success(request, 'Тема успешно создана!')
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = TopicForm()
    
    return render(request, 'forum/topic_form.html', {
        'form': form, 
        'section': section,
        'action': 'Создать'
    })

def topic_detail(request, topic_id):
    """Просмотр темы с сообщениями"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Уникальный счетчик просмотров с 6-часовым кулдауном
    if request.user.is_authenticated:
        from django.utils import timezone
        from datetime import timedelta
        from .models import TopicView
        
        # Проверяем, есть ли уже запись о просмотре от этого пользователя
        try:
            topic_view = TopicView.objects.get(topic=topic, user=request.user)
            # Проверяем, прошло ли 6 часов с последнего просмотра
            time_threshold = timezone.now() - timedelta(hours=6)
            if topic_view.view_date < time_threshold:
                # Обновляем время просмотра
                topic_view.view_date = timezone.now()
                topic_view.save(update_fields=['view_date'])
                # Увеличиваем счетчик просмотров
                topic.view_count += 1
                topic.save(update_fields=['view_count'])
        except TopicView.DoesNotExist:
            # Создаем новую запись о просмотре
            TopicView.objects.create(topic=topic, user=request.user)
            # Увеличиваем счетчик просмотров
            topic.view_count += 1
            topic.save(update_fields=['view_count'])
    else:
        # Для анонимных пользователей считаем каждый просмотр
        topic.view_count += 1
        topic.save(update_fields=['view_count'])
    
    # Получаем сообщения с пагинацией
    posts = Post.objects.filter(topic=topic, is_deleted=False).select_related('author').order_by('created_date')
    
    # Если пользователь авторизован, получаем информацию о лайках/дизлайках
    if request.user.is_authenticated:
        from .models import PostLike
        # Получаем все лайки/дизлайки пользователя для постов в этой теме
        user_likes = PostLike.objects.filter(
            post__in=posts,
            user=request.user
        ).values('post_id', 'like_type')
        
        # Создаем словарь для быстрого поиска
        user_likes_dict = {like['post_id']: like['like_type'] for like in user_likes}
        
        # Добавляем информацию о лайках к каждому посту
        for post in posts:
            post.user_liked = user_likes_dict.get(post.id) == 'like'
            post.user_disliked = user_likes_dict.get(post.id) == 'dislike'
    
    paginator = Paginator(posts, 25)  # 25 сообщений на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Проверяем, оценил ли пользователь тему
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = TopicRating.objects.get(topic=topic, user=request.user)
        except TopicRating.DoesNotExist:
            pass
    
    # Получаем теги темы
    topic_tags = Tag.objects.filter(topic_tags__topic=topic)
    
    # Конвертируем сообщения в Markdown
    for post in page_obj:
        post.content_html = mark_safe(markdown.markdown(post.content, extensions=['fenced_code', 'tables', 'nl2br']))
    
    context = {
        'topic': topic,
        'page_obj': page_obj,
        'user_rating': user_rating,
        'topic_tags': topic_tags,
    }
    return render(request, 'forum/topic_detail.html', context)


def members_list(request):
    """Список участников форума с поиском"""
    # Получаем всех пользователей с профилями
    users = User.objects.select_related('userprofile').filter(is_active=True).order_by('-date_joined')
    
    # Поиск пользователей
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(users, 20)  # 20 пользователей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'forum/members_list.html', context)

@login_required
def topic_edit(request, topic_id):
    """Редактирование темы (только автор или админ)"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Проверка прав
    if topic.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для редактирования этой темы.')
        return redirect('topic_detail', topic_id=topic_id)
    
    # Получаем первое сообщение темы
    first_post = Post.objects.filter(topic=topic, is_deleted=False).order_by('created_date').first()
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        # Always process the form data even if validation fails to see what's happening
        post_content = request.POST.get('post_content', '')
        
        if form.is_valid():
            form.save()
            
            # Обновляем теги
            tags = form.cleaned_data.get('tags', [])
            TopicTag.objects.filter(topic=topic).delete()
            for tag in tags:
                TopicTag.objects.create(topic=topic, tag=tag)
            
            # Обновляем содержание первого сообщения, если оно существует
            if first_post:
                if post_content != first_post.content:
                    first_post.content = post_content
                    first_post.edit_count += 1
                    from django.utils import timezone
                    first_post.last_edited_date = timezone.now()
                    first_post.save()
            
            messages.success(request, 'Тема успешно обновлена!')
            return redirect('topic_detail', topic_id=topic_id)
        else:
            # If form is not valid, add error messages
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            # Print form errors for debugging
            print("Form errors:", form.errors)
    else:
        form = TopicForm(instance=topic)
        # Загружаем существующие теги
        form.fields['tags'].initial = topic.topic_tags.all().values_list('tag_id', flat=True)
    
    # Передаем section и first_post в контекст для использования в шаблоне
    return render(request, 'forum/topic_form.html', {
        'form': form, 
        'topic': topic, 
        'section': topic.section,
        'first_post': first_post,
        'action': 'Редактировать'
    })

@login_required
@require_POST
def topic_delete(request, topic_id):
    """Удаление темы (только автор или админ)"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    # Проверка прав
    if topic.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для удаления этой темы.')
        return redirect('topic_detail', topic_id=topic_id)
    
    section_id = topic.section.id
    topic.delete()
    messages.success(request, 'Тема успешно удалена!')
    return redirect('topics_list', section_id=section_id)

# ========== СООБЩЕНИЯ (POSTS) ==========

@login_required
def post_create(request, topic_id):
    """Создание сообщения в теме"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            
            # Обновляем дату последнего сообщения в теме
            topic.last_post_date = post.created_date
            topic.save(update_fields=['last_post_date'])
            
            # Проверяем достижения после создания сообщения
            from .signals import check_post_achievements
            check_post_achievements(Post, post, created=True)
            
            messages.success(request, 'Сообщение успешно добавлено!')
            return redirect('topic_detail', topic_id=topic_id)
    else:
        form = PostForm()
    
    return render(request, 'forum/post_form.html', {'form': form, 'topic': topic, 'action': 'Создать'})

@login_required
def post_edit(request, post_id):
    """Редактирование сообщения (только автор или админ)"""
    post = get_object_or_404(Post, id=post_id)
    
    # Проверка прав
    if post.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для редактирования этого сообщения.')
        return redirect('topic_detail', topic_id=post.topic.id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.edit_count += 1
            from django.utils import timezone
            post.last_edited_date = timezone.now()
            post.save()
            
            messages.success(request, 'Сообщение успешно обновлено!')
            return redirect('topic_detail', topic_id=post.topic.id)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'forum/post_form.html', {'form': form, 'post': post, 'action': 'Редактировать'})

@login_required
@require_POST
def post_delete(request, post_id):
    """Удаление сообщения (только автор или админ)"""
    post = get_object_or_404(Post, id=post_id)
    topic_id = post.topic.id
    
    # Проверка прав
    if post.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для удаления этого сообщения.')
        return redirect('topic_detail', topic_id=topic_id)
    
    # Мягкое удаление
    post.is_deleted = True
    post.save(update_fields=['is_deleted'])
    
    messages.success(request, 'Сообщение успешно удалено!')
    return redirect('topic_detail', topic_id=topic_id)

# ========== API ДЛЯ ЛАЙКОВ И ОЦЕНОК ==========

@login_required
@require_POST
@csrf_protect
def post_like(request, post_id):
    """API для лайка/дизлайка сообщения"""
    post = get_object_or_404(Post, id=post_id)
    like_type = request.POST.get('like_type', 'like')  # 'like' или 'dislike'
    
    if like_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid like_type'}, status=400)
    
    # Проверяем, есть ли уже лайк от этого пользователя
    post_like_obj, created = PostLike.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'like_type': like_type}
    )
    
    # Получаем профиль автора поста для обновления кармы
    author_profile, _ = UserProfile.objects.get_or_create(user=post.author)
    
    if not created:
        # Если лайк уже существует, обновляем его
        if post_like_obj.like_type == like_type:
            # Если тот же тип, удаляем лайк
            old_type = post_like_obj.like_type
            post_like_obj.delete()
            
            # Обновляем счетчики
            if old_type == 'like':
                post.like_count = max(0, post.like_count - 1)
                # Уменьшаем карму автора поста
                author_profile.karma = max(0, author_profile.karma - 1)
            else:
                post.dislike_count = max(0, post.dislike_count - 1)
                # Увеличиваем карму автора поста (удаление дизлайка)
                author_profile.karma += 1
            post.save(update_fields=['like_count', 'dislike_count'])
            author_profile.save(update_fields=['karma'])
            
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'like_count': post.like_count,
                'dislike_count': post.dislike_count
            })
        else:
            # Меняем тип лайка
            old_type = post_like_obj.like_type
            post_like_obj.like_type = like_type
            post_like_obj.save()
            
            # Обновляем счетчики и карму
            if old_type == 'like':
                post.like_count = max(0, post.like_count - 1)
                post.dislike_count += 1
                # Уменьшаем карму на 2 (удаление лайка и добавление дизлайка)
                author_profile.karma = max(0, author_profile.karma - 2)
            else:
                post.dislike_count = max(0, post.dislike_count - 1)
                post.like_count += 1
                # Увеличиваем карму на 2 (удаление дизлайка и добавление лайка)
                author_profile.karma += 2
            post.save(update_fields=['like_count', 'dislike_count'])
            author_profile.save(update_fields=['karma'])
    else:
        # Новый лайк
        if like_type == 'like':
            post.like_count += 1
            # Увеличиваем карму автора поста
            author_profile.karma += 1
        else:
            post.dislike_count += 1
            # Уменьшаем карму автора поста
            author_profile.karma = max(0, author_profile.karma - 1)
        post.save(update_fields=['like_count', 'dislike_count'])
        author_profile.save(update_fields=['karma'])
    
    # Проверяем достижения, связанные с лайками
    from .signals import check_upvotes_achievements
    check_upvotes_achievements(post.author)
    
    return JsonResponse({
        'success': True,
        'action': 'added',
        'like_count': post.like_count,
        'dislike_count': post.dislike_count
    })

@login_required
@require_POST
@csrf_protect
def topic_rating(request, topic_id):
    """API для оценки темы (1-5 звезд)"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    try:
        rating_value = int(request.POST.get('rating', 0))
        if rating_value < 1 or rating_value > 5:
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid rating value'}, status=400)
    
    # Создаем или обновляем оценку
    topic_rating_obj, created = TopicRating.objects.get_or_create(
        topic=topic,
        user=request.user,
        defaults={'rating': rating_value}
    )
    
    if not created:
        topic_rating_obj.rating = rating_value
        topic_rating_obj.save()
    
    # Пересчитываем средний рейтинг
    ratings = TopicRating.objects.filter(topic=topic)
    topic.rating_count = ratings.count()
    topic.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0.0
    topic.save(update_fields=['rating_count', 'average_rating'])
    
    return JsonResponse({
        'success': True,
        'rating': rating_value,
        'average_rating': round(topic.average_rating, 2),
        'rating_count': topic.rating_count
    })

# ========== ТЕГИ (TAGS) ==========

def tags_list(request):
    """Список всех тегов с популярностью"""
    tags = Tag.objects.annotate(
        topics_count=Count('topic_tags')
    ).order_by('-topics_count')
    
    context = {
        'tags': tags,
    }
    return render(request, 'forum/tags_list.html', context)

@admin_required
def tag_create(request):
    """Создание нового тега (только для админов)"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#000000')
        
        if name:
            tag, created = Tag.objects.get_or_create(
                name=name,
                defaults={'color': color}
            )
            if created:
                messages.success(request, 'Тег успешно создан!')
            else:
                messages.error(request, 'Тег с таким именем уже существует.')
            return redirect('tags_list')
        else:
            messages.error(request, 'Название тега не может быть пустым.')
    
    return render(request, 'forum/tag_form.html', {'action': 'Создать'})

@admin_required
def tag_edit(request, tag_id):
    """Редактирование тега (только для админов)"""
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#000000')
        
        if name:
            # Проверяем, не занято ли имя другим тегом
            existing_tag = Tag.objects.filter(name=name).exclude(id=tag_id).first()
            if existing_tag:
                messages.error(request, 'Тег с таким именем уже существует.')
            else:
                tag.name = name
                tag.color = color
                tag.save()
                messages.success(request, 'Тег успешно обновлен!')
                return redirect('tags_list')
        else:
            messages.error(request, 'Название тега не может быть пустым.')
    
    return render(request, 'forum/tag_form.html', {'tag': tag, 'action': 'Редактировать'})

@admin_required
@require_POST
def tag_delete(request, tag_id):
    """Удаление тега (только для админов)"""
    tag = get_object_or_404(Tag, id=tag_id)
    tag.delete()
    messages.success(request, 'Тег успешно удален!')
    return redirect('tags_list')

def topics_by_tag(request, tag_id):
    """Фильтрация тем по тегу"""
    tag = get_object_or_404(Tag, id=tag_id)
    
    # Получаем темы с этим тегом
    topics = Topic.objects.filter(
        topic_tags__tag=tag
    ).annotate(
        posts_count=Count('post')
    ).order_by('-created_date')
    
    # Пагинация
    paginator = Paginator(topics, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
    }
    return render(request, 'forum/topics_by_tag.html', context)


def practice_view(request):
    """Страница практики"""
    return render(request, 'practice.html')


@login_required
def achievements_view(request):
    """Страница достижений пользователя"""
    user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    return render(request, 'achievements_list.html', {'user_achievements': user_achievements})
