from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg, Sum, Max
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
import markdown
import json
import logging
import re
import os
import shutil
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from .forms import CustomUserCreationForm, SectionForm, TopicForm, PostForm
from .models import (
    User, UserProfile, Section, Topic, Post, Tag, TopicTag, 
    Certificate, UserCertificate, Achievement, UserAchievement,
    UserRank, UserRankProgress, PostLike, TopicRating
)
from django.urls import reverse
from .decorators import admin_required
from django.http import Http404
from rest_framework.authtoken.models import Token
from urllib.parse import urlparse

User = get_user_model()

# Настройка логирования
logger = logging.getLogger(__name__)

ADMIN_ROLES = {
    'admin_level_1',
    'admin_level_2',
    'admin_level_3',
    'super_admin',
}

PROHIBITED_WORDS = [
    'бляд', 'сука', 'хуй', 'пизд', 'ебан', 'ебат', 'ебл', 'мраз', 'уёб', 'уеб',
    'пидор', 'пидр', 'запрет', 'нецензур', 'ругательств',
    'fuck', 'shit', 'bitch', 'cunt', 'asshole', 'бля', 
]

PROHIBITED_PATTERN = re.compile(r'(' + '|'.join(PROHIBITED_WORDS) + r')', re.IGNORECASE)

COMMISSION_RATE = Decimal('0.20')

PRACTICE_LANGUAGE_OPTIONS = [
    {'id': 'python', 'label': 'Python', 'cm_mode': 'python', 'file_ext': '.py'},
    {'id': 'ruby', 'label': 'Ruby', 'cm_mode': 'ruby', 'file_ext': '.rb'},
    {'id': 'cpp', 'label': 'C++', 'cm_mode': 'text/x-c++src', 'file_ext': '.cpp'},
    {'id': 'go', 'label': 'Go', 'cm_mode': 'go', 'file_ext': '.go'},
    {'id': 'csharp', 'label': 'C#', 'cm_mode': 'text/x-csharp', 'file_ext': '.cs'},
    {'id': 'javascript', 'label': 'JavaScript', 'cm_mode': 'javascript', 'file_ext': '.js'},
    {'id': 'java', 'label': 'Java', 'cm_mode': 'text/x-java', 'file_ext': '.java'},
    {'id': 'php', 'label': 'PHP', 'cm_mode': 'php', 'file_ext': '.php'},
    {'id': 'rust', 'label': 'Rust', 'cm_mode': 'rust', 'file_ext': '.rs'},
]
PRACTICE_LANGUAGE_MAP = {item['id']: item for item in PRACTICE_LANGUAGE_OPTIONS}

try:
    import bleach
    try:
        from bleach.css_sanitizer import CSSSanitizer
    except Exception:  # pragma: no cover
        CSSSanitizer = None
except Exception:  # pragma: no cover
    bleach = None
    CSSSanitizer = None

def _has_course_access(user, enrollment):
    """Paid access model with admin bypass."""
    return bool(enrollment and enrollment.is_paid) or _is_admin_user(user)

def _is_admin_user(user):
    """Checks both custom role and default Django flags."""
    return (
        getattr(user, 'role', None) in ADMIN_ROLES
        or user.is_staff
        or user.is_superuser
    )

def _is_moderator_user(user):
    """Check if user has moderator role"""
    return getattr(user, 'role', None) == 'moderator'

def _is_course_owner(user, course):
    return user.is_authenticated and course.creator_id == user.id

def _can_manage_course(user, course):
    return _is_course_owner(user, course) or _is_admin_user(user)

def _catalog_visible_courses_qs():
    from .models import Course
    return Course.objects.filter(is_active=True).filter(Q(status='approved') | Q(creator__isnull=True))

def _is_course_visible_in_catalog(course):
    return bool(course and course.is_active and (course.status == 'approved' or course.creator_id is None))

def _can_view_course(user, course):
    return _is_course_visible_in_catalog(course) or _can_manage_course(user, course)

def _contains_prohibited(text):
    if not text:
        return False
    return bool(PROHIBITED_PATTERN.search(text))

def _scan_course_for_prohibited(course):
    reasons = []
    if _contains_prohibited(course.title):
        reasons.append('Запрещенные слова в названии курса.')
    if _contains_prohibited(course.description):
        reasons.append('Запрещенные слова в описании курса.')
    if course.sections.exists():
        for section in course.sections.all():
            if _contains_prohibited(section.title) or _contains_prohibited(section.description):
                reasons.append(f'Запрещенные слова в разделе: {section.title}')
                break
    for lesson in course.lessons.all():
        if _contains_prohibited(lesson.title) or _contains_prohibited(lesson.content):
            reasons.append(f'Запрещенные слова в уроке: {lesson.title}')
            break
        if _contains_prohibited(getattr(lesson, 'practice_task', '')) or _contains_prohibited(getattr(lesson, 'practice_code_template', '')):
            reasons.append(f'Запрещенные слова в практике урока: {lesson.title}')
            break
        if getattr(lesson, 'test_cases', None):
            for tc in lesson.test_cases:
                if _contains_prohibited(tc.get('input', '')) or _contains_prohibited(tc.get('output', '')):
                    reasons.append(f'Запрещенные слова в тестах практики: {lesson.title}')
                    break
            if reasons:
                break
        for question in lesson.control_questions.all():
            if _contains_prohibited(question.prompt):
                reasons.append(f'Запрещенные слова в вопросе контрольной: {lesson.title}')
                break
            if _contains_prohibited(getattr(question, 'practice_input', '')) or _contains_prohibited(getattr(question, 'practice_output', '')):
                reasons.append(f'Запрещенные слова в практике контрольной: {lesson.title}')
                break
            for option in question.options.all():
                if _contains_prohibited(option.option_text):
                    reasons.append(f'Запрещенные слова в варианте ответа: {lesson.title}')
                    break
            if reasons:
                break
    return reasons

def _format_card_number(value):
    digits = re.sub(r'\D', '', value or '')[:16]
    return ' '.join([digits[i:i+4] for i in range(0, len(digits), 4)]).strip()


def _sanitize_rich_html(html_text):
    if not html_text:
        return ''
    if bleach is None:
        return html_text
    allowed_tags = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'span', 'blockquote',
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'pre', 'code', 'a', 'img',
        'video', 'source', 'mkv',
    ]
    allowed_attrs = {
        '*': ['style'],
        'a': ['href', 'target', 'rel', 'download'],
        'img': ['src', 'alt', 'title'],
        'video': ['src', 'controls', 'preload', 'poster', 'style'],
        'source': ['src', 'type'],
        'span': ['style'],
        'p': ['style'],
    }
    css_sanitizer = None
    if CSSSanitizer is not None:
        css_sanitizer = CSSSanitizer(
            allowed_css_properties=[
                'color', 'background-color', 'font-weight', 'font-style', 'text-decoration',
                'text-align', 'font-size'
            ]
        )
    clean = bleach.clean(
        html_text,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
        css_sanitizer=css_sanitizer,
    )
    return bleach.linkify(clean)


def _extract_valid_external_links(request):
    links = (request.POST.get('external_links') or '').splitlines()
    return [
        link.strip() for link in links
        if link.strip() and urlparse(link.strip()).scheme in ('http', 'https') and urlparse(link.strip()).netloc
    ]


def _create_link_attachments(request, target_obj, links):
    if not links:
        return []
    from .models import ContentAttachment
    ct = ContentType.objects.get_for_model(target_obj.__class__)
    created = []
    for link in links:
        created.append(ContentAttachment.objects.create(
            owner=request.user,
            content_type=ct,
            object_id=target_obj.id,
            kind='link',
            title=link[:120],
            external_url=link,
        ))
    return created


def _guess_attachment_kind(filename):
    lower = (filename or '').lower()
    if lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
        return 'image'
    # Browser-stable inline video formats.
    if lower.endswith(('.mp4', '.webm', '.ogv', '.ogg', '.m4v')):
        return 'video'
    return 'file'


def _create_attachments_from_request(request, target_obj):
    from .models import ContentAttachment
    files = request.FILES.getlist('attachments')
    if not files:
        return []
    created = []
    ct = ContentType.objects.get_for_model(target_obj.__class__)
    for f in files:
        kind = _guess_attachment_kind(getattr(f, 'name', ''))
        created.append(ContentAttachment.objects.create(
            owner=request.user,
            content_type=ct,
            object_id=target_obj.id,
            kind=kind,
            title=getattr(f, 'name', '')[:255],
            file=f,
        ))
    return created


def _delete_attachments_from_request(request, target_obj, ids_key='remove_attachment_ids'):
    from .models import ContentAttachment
    ids = [x for x in request.POST.getlist(ids_key) if str(x).isdigit()]
    if not ids:
        return 0
    ct = ContentType.objects.get_for_model(target_obj.__class__)
    qs = ContentAttachment.objects.filter(content_type=ct, object_id=target_obj.id, id__in=ids)
    deleted_count = qs.count()
    qs.delete()
    return deleted_count

@login_required
def moderator_panel_view(request):
    """
    Moderator panel with limited access to analytics, API docs, and CSV export
    """
    if not _is_moderator_user(request.user):
        messages.error(request, 'Доступ запрещен. Только для модераторов.')
        return redirect('home')
    
    from .models import Order
    revenue = Order.objects.filter(status='paid').exclude(payment_method='admin').aggregate(
        total_income=Sum('amount'),
        total_commission=Sum('commission_amount'),
        total_payout=Sum('payout_amount'),
    )
    context = {
        'revenue': revenue,
    }
    return render(request, 'moderator_panel.html', context)

@login_required
def moderator_purchases_view(request):
    from .models import Order

    if not _is_moderator_user(request.user) and not _is_admin_user(request.user):
        return redirect('home')

    orders = Order.objects.select_related('user', 'course', 'seller').order_by('-created_at')
    revenue = Order.objects.filter(status='paid').exclude(payment_method='admin').aggregate(
        total_income=Sum('amount'),
        total_commission=Sum('commission_amount'),
        total_payout=Sum('payout_amount'),
    )
    return render(request, 'education/purchases_dashboard.html', {
        'orders': orders,
        'revenue': revenue,
        'is_admin_view': False,
    })


def _build_course_analytics_context():
    from .models import Course, CourseEnrollment, CourseProgress, Order, CourseRating, CourseCategory, Lesson

    courses = list(
        Course.objects.filter(is_active=True)
        .select_related('category', 'creator')
        .order_by('title')
    )

    paid_orders_qs = Order.objects.filter(status='paid').exclude(payment_method='admin')
    revenue = paid_orders_qs.aggregate(
        total_income=Sum('amount'),
        total_commission=Sum('commission_amount'),
        total_payout=Sum('payout_amount'),
    )

    order_rows = paid_orders_qs.values('course_id').annotate(
        purchases=Count('id'),
        buyers=Count('user_id', distinct=True),
        revenue=Sum('amount'),
        avg_check=Avg('amount'),
        last_paid=Max('paid_at'),
    )
    orders_map = {row['course_id']: row for row in order_rows}

    ratings_rows = CourseRating.objects.values('course_id').annotate(
        avg_rating=Avg('rating'),
        rating_count=Count('id'),
    )
    ratings_map = {row['course_id']: row for row in ratings_rows}

    paid_enrollments = CourseEnrollment.objects.filter(is_paid=True).exclude(
        Q(user__role__in=ADMIN_ROLES) | Q(user__is_staff=True) | Q(user__is_superuser=True)
    ).values('course_id', 'user_id')
    completed_pairs = set(
        CourseProgress.objects.filter(is_completed=True).values_list('course_id', 'user_id')
    )
    enrolled_by_course = defaultdict(set)
    active_by_course = defaultdict(set)
    for row in paid_enrollments:
        cid = row['course_id']
        uid = row['user_id']
        enrolled_by_course[cid].add(uid)
        if (cid, uid) not in completed_pairs:
            active_by_course[cid].add(uid)

    completed_by_course = defaultdict(int)
    for cid, uid in completed_pairs:
        if uid in enrolled_by_course.get(cid, set()):
            completed_by_course[cid] += 1

    # meaningful progress from method-based value via per-row calculation
    course_ids = [course.id for course in courses]
    lessons_count_map = {
        row['course_id']: row['total']
        for row in Lesson.objects.filter(course_id__in=course_ids).values('course_id').annotate(total=Count('id'))
    }
    progress_sum_map = defaultdict(int)
    progress_count_map = defaultdict(int)
    progresses = CourseProgress.objects.filter(course_id__in=course_ids).prefetch_related('completed_lessons')
    for progress in progresses:
        total_lessons = lessons_count_map.get(progress.course_id, 0)
        if total_lessons == 0:
            pct = 0
        else:
            pct = int((len(progress.completed_lessons.all()) / total_lessons) * 100)
        progress_sum_map[progress.course_id] += pct
        progress_count_map[progress.course_id] += 1
    progress_map = {}
    for cid in course_ids:
        count = progress_count_map.get(cid, 0)
        progress_map[cid] = round(progress_sum_map.get(cid, 0) / count, 1) if count else 0

    course_rows = []
    for course in courses:
        order_data = orders_map.get(course.id, {})
        rating_data = ratings_map.get(course.id, {})
        enrolled_count = len(enrolled_by_course.get(course.id, set()))
        completed_count = completed_by_course.get(course.id, 0)
        active_count = len(active_by_course.get(course.id, set()))
        completion_rate = round((completed_count / enrolled_count) * 100, 1) if enrolled_count else 0
        course_rows.append({
            'course': course,
            'purchases': order_data.get('purchases', 0) or 0,
            'buyers': order_data.get('buyers', 0) or 0,
            'revenue': order_data.get('revenue', Decimal('0.00')) or Decimal('0.00'),
            'avg_check': order_data.get('avg_check', Decimal('0.00')) or Decimal('0.00'),
            'last_paid': order_data.get('last_paid'),
            'enrolled': enrolled_count,
            'active': active_count,
            'completed': completed_count,
            'completion_rate': completion_rate,
            'avg_progress': progress_map.get(course.id, 0),
            'avg_rating': round(rating_data.get('avg_rating') or 0, 2),
            'rating_count': rating_data.get('rating_count', 0) or 0,
        })

    course_rows.sort(key=lambda row: (row['revenue'], row['buyers']), reverse=True)

    category_rows = list(
        CourseCategory.objects.annotate(
            total_courses=Count('courses', filter=Q(courses__is_active=True)),
            paid_orders=Count('courses__orders', filter=Q(courses__orders__status='paid') & ~Q(courses__orders__payment_method='admin')),
            revenue=Sum(
                'courses__orders__amount',
                filter=Q(courses__orders__status='paid') & ~Q(courses__orders__payment_method='admin')
            ),
        ).order_by('-revenue', 'name')
    )

    daily_revenue = list(
        paid_orders_qs.filter(paid_at__isnull=False)
        .annotate(day=TruncDate('paid_at'))
        .values('day')
        .annotate(
            revenue=Sum('amount'),
            purchases=Count('id'),
            buyers=Count('user_id', distinct=True),
        )
        .order_by('-day')[:30]
    )
    daily_revenue.reverse()

    total_enrolled = sum(len(v) for v in enrolled_by_course.values())
    total_active = sum(len(v) for v in active_by_course.values())
    total_completed = sum(completed_by_course.values())
    completion_rate_global = round((total_completed / total_enrolled) * 100, 1) if total_enrolled else 0

    totals = {
        'total_courses': len(courses),
        'total_buyers': paid_orders_qs.values('user_id').distinct().count(),
        'total_purchases': paid_orders_qs.count(),
        'total_active_learners': total_active,
        'total_completed_learners': total_completed,
        'global_completion_rate': completion_rate_global,
    }

    return {
        'revenue': revenue,
        'totals': totals,
        'course_rows': course_rows,
        'category_rows': category_rows,
        'daily_revenue': daily_revenue,
    }


@login_required
def moderator_course_analytics_view(request):
    if not _is_moderator_user(request.user) and not _is_admin_user(request.user):
        return redirect('home')
    context = _build_course_analytics_context()
    context['is_admin_view'] = False
    return render(request, 'education/course_analytics_dashboard.html', context)

def custom_404_view(request, exception):
    """
    Кастомная страница 404 ошибки
    """
    return render(request, '404.html', status=404)

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
    latest_topics = Topic.objects.select_related('section', 'author').prefetch_related('topic_tags__tag').order_by('-created_date')[:6]
    
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

def privacy_policy_view(request):
    """
    View function for displaying privacy policy
    """
    return render(request, 'privacy_policy.html')

@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    View function for handling password reset requests
    """
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Используем filter().first() вместо get() для обработки случаев с несколькими пользователями
            user = User.objects.filter(email=email).first()
            
            if user:
                # Генерируем токен
                token = default_token_generator.make_token(user)
                # Кодируем ID пользователя в base64
                uid_bytes = force_bytes(str(user.pk))
                uid = urlsafe_base64_encode(uid_bytes)
                
                # Создаем ссылку для сброса пароля
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Отправляем email
                subject = 'Восстановление пароля - Plekhanov CourseHub'
                message = render_to_string('password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'Plekhanov CourseHub',
                })
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@gadukagang.com',
                        [email],
                        html_message=message,
                        fail_silently=False,
                    )
                except Exception as e:
                    # Логируем ошибку, но не показываем пользователю (безопасность)
                    logger.error(f'Ошибка отправки email для восстановления пароля: {str(e)}', exc_info=True)
                    # В режиме разработки можно показать предупреждение администратору
                    if settings.DEBUG:
                        messages.warning(request, f'Ошибка отправки email. Проверьте настройки SMTP. Ошибка: {str(e)}')
            
            # Не показываем, существует ли пользователь (безопасность)
            # Всегда показываем успешное сообщение, даже если пользователь не найден
            messages.success(request, 'Если аккаунт с таким email существует, инструкции по восстановлению пароля отправлены.')
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()
    
    return render(request, 'password_reset_form.html', {'form': form})

def password_reset_done_view(request):
    """
    View function for displaying password reset done message
    """
    return render(request, 'password_reset_done.html')

@require_http_methods(["GET", "POST"])
def password_reset_confirm(request, uidb64, token):
    """
    View function for handling password reset confirmation
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.')
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'password_reset_confirm.html', {'validlink': False})

def password_reset_complete_view(request):
    """
    View function for displaying password reset complete message
    """
    return render(request, 'password_reset_complete.html')

@login_required
def profile_view(request):
    """Просмотр профиля пользователя"""
    # Получаем или создаем профиль пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Получаем сертификаты пользователя
    user_certificates = UserCertificate.objects.filter(user=request.user).select_related('certificate')
    
    # Получаем достижения пользователя
    user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement').order_by('-earned_date')
    
    # Обновляем количество сообщений пользователя
    post_count = Post.objects.filter(author=request.user, is_deleted=False).count()
    user_profile.post_count = post_count
    user_profile.save(update_fields=['post_count'])
    
    from .models import CourseFavorite
    favorites_count = CourseFavorite.objects.filter(user=request.user).count()

    context = {
        'user_profile': user_profile,
        'user_certificates': user_certificates,
        'user_achievements': user_achievements,
        'is_admin_user': _is_admin_user(request.user),
        'favorites_count': favorites_count,
    }
    return render(request, 'profile.html', context)


@login_required
@require_POST
def toggle_favorite_course(request, course_id):
    from .models import Course, CourseFavorite

    course = get_object_or_404(Course, id=course_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not _is_course_visible_in_catalog(course):
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Курс недоступен для избранного.'}, status=400)
        messages.error(request, 'Курс недоступен для избранного.')
        return redirect('profile_favorites')

    favorite, created = CourseFavorite.objects.get_or_create(user=request.user, course=course)
    if created:
        if is_ajax:
            return JsonResponse({'success': True, 'action': 'added'})
        messages.success(request, 'Курс добавлен в избранное.')
        return redirect('profile_favorites')
    favorite.delete()
    if is_ajax:
        return JsonResponse({'success': True, 'action': 'removed'})
    messages.success(request, 'Курс удален из избранного.')
    return redirect('profile_favorites')


@login_required
def profile_favorites_view(request):
    from .models import CourseFavorite

    favorites = CourseFavorite.objects.filter(user=request.user).select_related('course', 'course__category').order_by('-created_at')
    return render(request, 'education/profile_favorites.html', {'favorites': favorites})


def certificate_verify_view(request, code):
    cert = UserCertificate.objects.filter(verification_code=code).select_related('user', 'certificate').first()
    context = {
        'valid': cert is not None,
        'user_certificate': cert,
        'lookup_code': code,
    }
    return render(request, 'education/certificate_verify.html', context)


def certificate_verify_lookup_view(request):
    code = (request.GET.get('code') or '').strip()
    if code:
        return redirect('certificate_verify', code=code)
    return render(request, 'education/certificate_verify.html', {
        'valid': None,
        'user_certificate': None,
        'lookup_code': '',
    })


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
            'total_users': total_users,
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
    return render(request, 'profile_guest.html', context)

@login_required
@require_POST
def unlock_admin_token(request):
    """Возвращает админский токен после подтверждения пароля"""
    if not _is_admin_user(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = request.POST

    password = payload.get('password', '').strip()
    if not password:
        return JsonResponse({'error': 'Введите пароль'}, status=400)

    if not request.user.check_password(password):
        return JsonResponse({'error': 'Неверный пароль'}, status=400)

    token, _ = Token.objects.get_or_create(user=request.user)
    return JsonResponse({'token': token.key})

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
        { 'name': 'Оценки курсов', 'url': reverse('admin:GadukaGang_courserating_changelist') },
        { 'name': 'Подписки на пользователей', 'url': reverse('admin:GadukaGang_usersubscription_changelist') },
        { 'name': 'Подписки на темы', 'url': reverse('admin:GadukaGang_topicsubscription_changelist') },
        { 'name': 'Действия модераторов', 'url': reverse('admin:GadukaGang_moderatoraction_changelist') },
        { 'name': 'Логи администраторов', 'url': reverse('admin:GadukaGang_adminlog_changelist') },
        { 'name': 'Уведомления', 'url': reverse('admin:GadukaGang_notification_changelist') },
        { 'name': 'Поисковый индекс', 'url': reverse('admin:GadukaGang_searchindex_changelist') },
        { 'name': 'GitHub OAuth', 'url': reverse('admin:GadukaGang_githubauth_changelist') },
    ]

    from .models import Order
    revenue = Order.objects.filter(status='paid').exclude(payment_method='admin').aggregate(
        total_income=Sum('amount'),
        total_commission=Sum('commission_amount'),
        total_payout=Sum('payout_amount'),
    )
    context = {
        'admin_links': admin_links,
        'revenue': revenue,
    }
    return render(request, 'admin_panel.html', context)

@admin_required
def admin_purchases_view(request):
    from .models import Order

    orders = Order.objects.select_related('user', 'course', 'seller').order_by('-created_at')
    revenue = Order.objects.filter(status='paid').exclude(payment_method='admin').aggregate(
        total_income=Sum('amount'),
        total_commission=Sum('commission_amount'),
        total_payout=Sum('payout_amount'),
    )
    return render(request, 'education/purchases_dashboard.html', {
        'orders': orders,
        'revenue': revenue,
        'is_admin_view': True,
    })


@admin_required
def admin_course_analytics_view(request):
    context = _build_course_analytics_context()
    context['is_admin_view'] = True
    return render(request, 'education/course_analytics_dashboard.html', context)

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
        data = request.POST.copy()
        data['section'] = str(section.id)
        form = TopicForm(data)
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
            post_content = _sanitize_rich_html(request.POST.get('post_content', ''))
            external_links = _extract_valid_external_links(request)
            has_files = bool(request.FILES.getlist('attachments'))
            if post_content or has_files or external_links:
                first_post = Post.objects.create(
                    topic=topic,
                    author=request.user,
                    content=post_content or '<p>Вложение</p>'
                )
                _create_attachments_from_request(request, first_post)
                _create_link_attachments(request, first_post, external_links)
            
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
    
    # Проверяем, связана ли тема с сообществом
    community = None
    try:
        from .models import CommunityTopic
        community_topic = CommunityTopic.objects.filter(topic=topic).select_related('community').first()
        if community_topic:
            community = community_topic.community
    except:
        pass
    
    from .models import ContentAttachment
    post_ids = [p.id for p in page_obj]
    attachments_map = {}
    if post_ids:
        post_ct = ContentType.objects.get_for_model(Post)
        for item in ContentAttachment.objects.filter(content_type=post_ct, object_id__in=post_ids).order_by('created_at'):
            attachments_map.setdefault(item.object_id, []).append(item)

    # Конвертируем сообщения в Markdown
    for post in page_obj:
        post.content_html = mark_safe(markdown.markdown(post.content, extensions=['fenced_code', 'tables', 'nl2br']))
        post.attachments = attachments_map.get(post.id, [])
    
    context = {
        'topic': topic,
        'page_obj': page_obj,
        'user_rating': user_rating,
        'topic_tags': topic_tags,
        'community': community,
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
    existing_attachments = []
    if first_post:
        from .models import ContentAttachment
        post_ct = ContentType.objects.get_for_model(first_post.__class__)
        existing_attachments = list(
            ContentAttachment.objects.filter(content_type=post_ct, object_id=first_post.id).order_by('-created_at')
        )
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        # Always process the form data even if validation fails to see what's happening
        post_content = _sanitize_rich_html(request.POST.get('post_content', ''))
        
        if form.is_valid():
            form.save()
            
            # Обновляем теги
            tags = form.cleaned_data.get('tags', [])
            TopicTag.objects.filter(topic=topic).delete()
            for tag in tags:
                TopicTag.objects.create(topic=topic, tag=tag)
            
            external_links = _extract_valid_external_links(request)
            has_files = bool(request.FILES.getlist('attachments'))

            # Обновляем содержание первого сообщения, если оно существует
            if first_post:
                if post_content != first_post.content:
                    first_post.content = post_content
                    first_post.edit_count += 1
                    from django.utils import timezone
                    first_post.last_edited_date = timezone.now()
                    first_post.save()
                _delete_attachments_from_request(request, first_post)
                if has_files:
                    _create_attachments_from_request(request, first_post)
                if external_links:
                    _create_link_attachments(request, first_post, external_links)
            elif post_content or has_files or external_links:
                first_post = Post.objects.create(
                    topic=topic,
                    author=request.user,
                    content=post_content or '<p>Вложение</p>'
                )
                if has_files:
                    _create_attachments_from_request(request, first_post)
                if external_links:
                    _create_link_attachments(request, first_post, external_links)
            
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
        'existing_attachments': existing_attachments,
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
    
    # Проверяем, связана ли тема с сообществом
    from .models import CommunityTopic
    community_topic = CommunityTopic.objects.filter(topic=topic).first()
    
    section_id = topic.section.id
    topic.delete()
    messages.success(request, 'Тема успешно удалена!')
    
    # Редиректим обратно
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    elif community_topic:
        return redirect('community_detail', community_id=community_topic.community.id)
    else:
        return redirect('topics_list', section_id=section_id)

# ========== СООБЩЕНИЯ (POSTS) ==========

@login_required
def post_create(request, topic_id):
    """Создание сообщения в теме"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        has_files = bool(request.FILES.getlist('attachments'))
        if form.is_valid() or has_files:
            if form.is_valid():
                post = form.save(commit=False)
                post_content = _sanitize_rich_html(getattr(post, 'content', ''))
            else:
                post = Post(topic=topic, author=request.user)
                post_content = ''
            post.topic = topic
            post.author = request.user
            post.content = post_content or '<p>Вложение</p>'
            post.save()
            _create_attachments_from_request(request, post)
            
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
    from .models import ContentAttachment

    post = get_object_or_404(Post, id=post_id)
    
    # Проверка прав
    if post.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'У вас нет прав для редактирования этого сообщения.')
        return redirect('topic_detail', topic_id=post.topic.id)
    
    # Проверяем, связана ли тема с сообществом
    from .models import CommunityTopic
    community_topic = CommunityTopic.objects.filter(topic=post.topic).first()
    redirect_url = 'topic_detail'
    redirect_kwargs = {'topic_id': post.topic.id}
    
    if community_topic:
        # Если тема в сообществе, редиректим на страницу сообщества после редактирования
        redirect_url = 'community_detail'
        redirect_kwargs = {'community_id': community_topic.community.id}
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.content = _sanitize_rich_html(post.content)
            post.edit_count += 1
            from django.utils import timezone
            post.last_edited_date = timezone.now()
            post.save()
            _delete_attachments_from_request(request, post)
            _create_attachments_from_request(request, post)
            
            messages.success(request, 'Сообщение успешно обновлено!')
            # Редиректим обратно на тему, но если есть next параметр - используем его
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(redirect_url, **redirect_kwargs)
    else:
        form = PostForm(instance=post)
    
    # Передаем информацию о сообществе в контекст
    context = {
        'form': form, 
        'post': post, 
        'action': 'Редактировать',
        'community': community_topic.community if community_topic else None,
        'topic': post.topic,
        'post_attachments': list(
            ContentAttachment.objects.filter(
                content_type=ContentType.objects.get_for_model(post.__class__),
                object_id=post.id,
            ).order_by('-created_at')
        ),
    }
    return render(request, 'forum/post_form.html', context)

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
    
    # Проверяем, связана ли тема с сообществом
    from .models import CommunityTopic
    community_topic = CommunityTopic.objects.filter(topic=post.topic).first()
    
    # Мягкое удаление
    post.is_deleted = True
    post.save(update_fields=['is_deleted'])
    
    messages.success(request, 'Сообщение успешно удалено!')
    
    # Редиректим обратно на тему
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    elif community_topic:
        return redirect('community_detail', community_id=community_topic.community.id)
    else:
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


@login_required
@require_POST
def course_rating(request, course_id):
    from .models import Course, CourseEnrollment, CourseRating

    course = get_object_or_404(Course, id=course_id, is_active=True)
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course, is_paid=True).first()
    if not enrollment:
        return JsonResponse({'error': 'Оценку может оставить только пользователь, купивший курс.'}, status=403)

    try:
        rating_value = int(request.POST.get('rating', 0))
        if rating_value < 1 or rating_value > 5:
            return JsonResponse({'error': 'Оценка должна быть от 1 до 5'}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Некорректное значение оценки'}, status=400)

    rating_obj, created = CourseRating.objects.get_or_create(
        course=course,
        user=request.user,
        defaults={'rating': rating_value},
    )
    if not created:
        rating_obj.rating = rating_value
        rating_obj.save(update_fields=['rating', 'updated_at'])

    agg = CourseRating.objects.filter(course=course).aggregate(avg=Avg('rating'), cnt=Count('id'))
    return JsonResponse({
        'success': True,
        'rating': rating_value,
        'average_rating': round(agg['avg'] or 0, 2),
        'rating_count': agg['cnt'] or 0,
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
    """Страница образования (заменяет практику)"""
    return render(request, 'education.html')

def education_view(request):
    """Course catalog with search and categories"""
    from .models import Course, CourseProgress, CourseCategory, CourseEnrollment

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    page_number = request.GET.get('page', 1)

    courses_qs = Course.objects.filter(is_active=True).select_related('category')
    if not (request.user.is_authenticated and _is_admin_user(request.user)):
        courses_qs = _catalog_visible_courses_qs().select_related('category')
    if query:
        courses_qs = courses_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    if category_id:
        courses_qs = courses_qs.filter(category_id=category_id)

    courses = courses_qs.order_by('order').prefetch_related('lessons', 'sections')
    categories = CourseCategory.objects.order_by('order', 'name')

    courses_with_progress = []
    user_progress_dict = {}
    enrollment_dict = {}

    if request.user.is_authenticated:
        enrollments = CourseEnrollment.objects.filter(user=request.user)
        enrollment_dict = {en.course_id: en for en in enrollments}

        progresses = CourseProgress.objects.filter(user=request.user).select_related('course').prefetch_related('completed_lessons')
        for progress in progresses:
            total_lessons = progress.course.lessons.count()
            completed_count = progress.completed_lessons.count()
            user_progress_dict[progress.course.id] = {
                'progress': progress.get_progress_percentage(),
                'is_completed': progress.is_completed,
                'completed_lessons_count': completed_count,
                'total_lessons': total_lessons,
            }

    for course in courses:
        progress_data = user_progress_dict.get(course.id)
        enrollment = enrollment_dict.get(course.id)
        has_access = _has_course_access(request.user, enrollment)
        courses_with_progress.append({
            'course': course,
            'progress': progress_data,
            'enrollment': enrollment,
            'has_access': has_access,
        })

    paginator = Paginator(courses_with_progress, 12)
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    if 'partial' in query_params:
        query_params.pop('partial')
    base_querystring = query_params.urlencode()

    context = {
        'courses_with_progress': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.paginator.num_pages > 1,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'base_querystring': base_querystring,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'is_admin_user': request.user.is_authenticated and _is_admin_user(request.user),
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('partial') == 'courses':
        return render(request, 'education/partials/course_cards.html', context)

    return render(request, 'education/education.html', context)


@login_required
def creator_courses_view(request):
    from .models import Course, Order

    courses = Course.objects.filter(creator=request.user).order_by('-created_date')
    paid_stats = (
        Order.objects.filter(course__in=courses, status='paid')
        .values('course_id')
        .annotate(
            orders_count=Count('id'),
            revenue=Sum('amount'),
            commission=Sum('commission_amount'),
            payout=Sum('payout_amount'),
        )
    )
    stats_map = {row['course_id']: row for row in paid_stats}

    courses_data = []
    for course in courses:
        stats = stats_map.get(course.id, {})
        courses_data.append({
            'course': course,
            'orders_count': stats.get('orders_count', 0) or 0,
            'revenue': stats.get('revenue', 0) or 0,
            'commission': stats.get('commission', 0) or 0,
            'payout': stats.get('payout', 0) or 0,
        })

    return render(request, 'education/creator_courses.html', {
        'courses_data': courses_data,
    })


@login_required
@require_http_methods(["GET", "POST"])
def creator_course_create(request):
    from .models import Course, CourseCategory

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0').strip() or '0'
        category_id = request.POST.get('category')
        level = request.POST.get('level', 'Начальный').strip() or 'Начальный'
        duration_weeks = int(request.POST.get('duration_weeks', '0') or 0)
        payout_method = request.POST.get('payout_method', '').strip()
        payout_details = request.POST.get('payout_details', '').strip()
        payout_sbp_phone = request.POST.get('payout_sbp_phone', '').strip()
        payout_card_number = request.POST.get('payout_card_number', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()

        has_error = False
        if not title or not description:
            messages.error(request, 'Укажите название и описание курса.')
            has_error = True
        if payout_method == 'sbp':
            if not payout_sbp_phone:
                messages.error(request, 'Укажите телефон для СБП.')
                has_error = True
            else:
                payout_details = payout_sbp_phone
        elif payout_method == 'card':
            formatted = _format_card_number(payout_card_number)
            if len(formatted.replace(' ', '')) != 16:
                messages.error(request, 'Номер карты должен содержать 16 цифр.')
                has_error = True
            else:
                payout_details = formatted
        elif payout_method == 'bank':
            if not payout_details:
                messages.error(request, 'Укажите банковские реквизиты.')
                has_error = True
        else:
            payout_details = ''

        if not has_error:
            course = Course.objects.create(
                creator=request.user,
                title=title,
                description=description,
                price=Decimal(price),
                category_id=category_id if category_id else None,
                level=level,
                duration_weeks=duration_weeks,
                payout_method=payout_method,
                payout_details=payout_details,
                contact_email=contact_email,
                contact_phone=contact_phone,
                status='draft',
            )
            messages.success(request, 'Курс создан. Заполните программу.')
            return redirect('creator_course_builder', course_id=course.id)

    categories = CourseCategory.objects.order_by('order', 'name')
    return render(request, 'education/creator_course_form.html', {
        'categories': categories,
        'is_edit': False,
    })


@login_required
@require_http_methods(["GET", "POST"])
def creator_course_edit(request, course_id):
    from .models import Course, CourseCategory

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return redirect('creator_courses')

    if request.method == 'POST':
        course.title = request.POST.get('title', '').strip()
        course.description = request.POST.get('description', '').strip()
        course.price = Decimal(request.POST.get('price', '0') or 0)
        course.category_id = request.POST.get('category') or None
        course.level = request.POST.get('level', 'Начальный').strip() or 'Начальный'
        course.duration_weeks = int(request.POST.get('duration_weeks', '0') or 0)
        course.payout_method = request.POST.get('payout_method', '').strip()
        payout_details = request.POST.get('payout_details', '').strip()
        payout_sbp_phone = request.POST.get('payout_sbp_phone', '').strip()
        payout_card_number = request.POST.get('payout_card_number', '').strip()
        course.contact_email = request.POST.get('contact_email', '').strip()
        course.contact_phone = request.POST.get('contact_phone', '').strip()
        has_error = False
        if course.payout_method == 'sbp':
            if not payout_sbp_phone:
                messages.error(request, 'Укажите телефон для СБП.')
                has_error = True
            else:
                course.payout_details = payout_sbp_phone
        elif course.payout_method == 'card':
            formatted = _format_card_number(payout_card_number)
            if len(formatted.replace(' ', '')) != 16:
                messages.error(request, 'Номер карты должен содержать 16 цифр.')
                has_error = True
            else:
                course.payout_details = formatted
        elif course.payout_method == 'bank':
            if not payout_details:
                messages.error(request, 'Укажите банковские реквизиты.')
                has_error = True
            else:
                course.payout_details = payout_details
        else:
            course.payout_details = ''

        if not has_error:
            course.save()
            messages.success(request, 'Курс обновлен.')
            return redirect('creator_course_builder', course_id=course.id)

    categories = CourseCategory.objects.order_by('order', 'name')
    return render(request, 'education/creator_course_form.html', {
        'course': course,
        'categories': categories,
        'is_edit': True,
    })


@login_required
def creator_course_builder(request, course_id):
    from .models import Course, CourseSection, Lesson

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return redirect('creator_courses')

    sections = CourseSection.objects.filter(course=course).prefetch_related('lessons').order_by('order')
    free_lessons = Lesson.objects.filter(course=course, section__isnull=True).order_by('order')

    return render(request, 'education/course_builder.html', {
        'course': course,
        'sections': sections,
        'free_lessons': free_lessons,
    })


@login_required
@require_POST
def creator_reorder_sections(request, course_id):
    from .models import Course, CourseSection

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return JsonResponse({'success': False}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False}, status=400)

    section_ids = payload.get('sections', [])
    for idx, section_id in enumerate(section_ids, start=1):
        CourseSection.objects.filter(id=section_id, course=course).update(order=idx)
    return JsonResponse({'success': True})


@login_required
@require_POST
def creator_reorder_lessons(request, course_id):
    from .models import Course, Lesson, CourseSection

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return JsonResponse({'success': False}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False}, status=400)

    mapping = payload.get('mapping', {})
    for section_key, lesson_ids in mapping.items():
        section_id = None if section_key == 'none' else int(section_key)
        if section_id:
            CourseSection.objects.filter(id=section_id, course=course).exists()
        for idx, lesson_id in enumerate(lesson_ids, start=1):
            Lesson.objects.filter(id=lesson_id, course=course).update(section_id=section_id, order=idx)
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET", "POST"])
def creator_section_create(request, course_id):
    from .models import Course, CourseSection

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return redirect('creator_courses')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        order = int(request.POST.get('order', '0') or 0)
        if not title:
            messages.error(request, 'Введите название блока.')
        else:
            CourseSection.objects.create(
                course=course,
                title=title,
                description=description,
                order=order,
            )
            messages.success(request, 'Блок добавлен.')
            return redirect('creator_course_builder', course_id=course.id)

    return render(request, 'education/creator_section_form.html', {
        'course': course,
        'is_edit': False,
    })


@login_required
@require_http_methods(["GET", "POST"])
def creator_section_edit(request, section_id):
    from .models import CourseSection

    section = get_object_or_404(CourseSection, id=section_id)
    if not _can_manage_course(request.user, section.course):
        return redirect('creator_courses')

    if request.method == 'POST':
        section.title = request.POST.get('title', '').strip()
        section.description = request.POST.get('description', '').strip()
        section.order = int(request.POST.get('order', '0') or 0)
        section.save()
        messages.success(request, 'Блок обновлен.')
        return redirect('creator_course_builder', course_id=section.course.id)

    return render(request, 'education/creator_section_form.html', {
        'course': section.course,
        'section': section,
        'is_edit': True,
    })


@login_required
@require_POST
def creator_section_delete(request, section_id):
    from .models import CourseSection

    section = get_object_or_404(CourseSection, id=section_id)
    if not _can_manage_course(request.user, section.course):
        return redirect('creator_courses')
    course_id = section.course.id
    section.delete()
    messages.success(request, 'Блок удален.')
    return redirect('creator_course_builder', course_id=course_id)


@login_required
@require_http_methods(["GET", "POST"])
def creator_lesson_create(request, course_id):
    from .models import Course, CourseSection, Lesson

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return redirect('creator_courses')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = _sanitize_rich_html(request.POST.get('content', '').strip())
        lesson_type = request.POST.get('lesson_type', 'lecture')
        practice_mode = request.POST.get('practice_mode', 'code')
        section_id = request.POST.get('section') or None
        order = int(request.POST.get('order', '0') or 0)
        practice_code_template = request.POST.get('practice_code_template', '').strip()
        practice_task = request.POST.get('practice_task', '').strip()
        test_cases_raw = request.POST.get('test_cases', '').strip()
        control_pass_threshold = int(request.POST.get('control_pass_threshold', '70') or 70)
        control_lock_minutes = int(request.POST.get('control_lock_minutes', '10') or 10)
        control_time_limit_minutes = int(request.POST.get('control_time_limit_minutes', '30') or 30)

        test_cases = []
        control_questions_raw = request.POST.get('control_questions_json', '').strip()

        is_it = True if course.category is None else bool(getattr(course.category, 'is_it', False))
        posted_testcases = bool(request.POST.getlist('testcase_input') or request.POST.getlist('testcase_output'))
        if lesson_type == 'control':
            practice_mode = 'quiz'
        elif lesson_type == 'practice':
            if posted_testcases:
                practice_mode = 'code'
            elif not is_it:
                practice_mode = 'quiz'

        if lesson_type == 'practice':
            if test_cases_raw:
                try:
                    test_cases = json.loads(test_cases_raw)
                except json.JSONDecodeError:
                    test_cases = []
            if not test_cases:
                inputs = request.POST.getlist('testcase_input')
                outputs = request.POST.getlist('testcase_output')
                test_cases = [
                    {'input': inp, 'output': out}
                    for inp, out in zip(inputs, outputs)
                    if (inp or out)
                ]
            if practice_mode != 'code':
                test_cases = []
            # Debug logging for practice test saves
            try:
                debug_path = settings.BASE_DIR / 'practice_save_debug.log'
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"[CREATE] lesson_type={lesson_type} practice_mode={practice_mode} is_it={is_it} "
                            f"posted_testcases={posted_testcases} raw_len={len(test_cases_raw)} "
                            f"parsed_count={len(test_cases)} inputs={len(request.POST.getlist('testcase_input'))} "
                            f"outputs={len(request.POST.getlist('testcase_output'))}\n")
            except Exception:
                pass
        else:
            practice_code_template = ''
            practice_task = ''

        if not title:
            messages.error(request, 'Введите название урока.')
        else:
            lesson = Lesson.objects.create(
                course=course,
                section_id=section_id,
                title=title,
                content=content,
                lesson_type=lesson_type,
                practice_mode=practice_mode,
                order=order,
                practice_code_template=practice_code_template,
                practice_task=practice_task,
                test_cases=test_cases,
                control_pass_threshold=control_pass_threshold,
                control_lock_minutes=control_lock_minutes,
                control_time_limit_minutes=control_time_limit_minutes,
            )
            if lesson_type == 'control' or (lesson_type == 'practice' and practice_mode == 'quiz'):
                questions_payload = []
                if control_questions_raw:
                    try:
                        questions_payload = json.loads(control_questions_raw)
                    except json.JSONDecodeError:
                        questions_payload = []
                from .models import ControlQuestion, ControlQuestionOption
                for q_index, q in enumerate(questions_payload, start=1):
                    question_kind = q.get('question_kind', 'theory')
                    if lesson_type == 'practice':
                        question_kind = 'theory'
                    question = ControlQuestion.objects.create(
                        lesson=lesson,
                        prompt=q.get('prompt', ''),
                        question_type=q.get('question_type', 'single'),
                        question_kind=question_kind,
                        practice_input=q.get('practice_input', ''),
                        practice_output=q.get('practice_output', ''),
                        order=q_index,
                        weight=int(q.get('weight') or 1),
                        min_words=int(q.get('min_words') or 20),
                        required_keywords=q.get('required_keywords') or [],
                    )
                    options = q.get('options') or []
                    for o_index, opt in enumerate(options, start=1):
                        ControlQuestionOption.objects.create(
                            question=question,
                            option_text=opt.get('option_text', ''),
                            is_correct=bool(opt.get('is_correct')),
                            order=o_index,
                        )
            _create_attachments_from_request(request, lesson)
            messages.success(request, 'Урок добавлен.')
            return redirect('creator_course_builder', course_id=course.id)

    sections = CourseSection.objects.filter(course=course).order_by('order')
    return render(request, 'education/creator_lesson_form.html', {
        'course': course,
        'sections': sections,
        'is_it_course': True if course.category is None else bool(getattr(course.category, 'is_it', False)),
        'is_edit': False,
        'control_questions_json': [],
    })


@login_required
@require_http_methods(["GET", "POST"])
def creator_lesson_edit(request, lesson_id):
    from .models import Lesson, CourseSection

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not _can_manage_course(request.user, lesson.course):
        return redirect('creator_courses')

    if request.method == 'POST':
        lesson.title = request.POST.get('title', '').strip()
        lesson.content = _sanitize_rich_html(request.POST.get('content', '').strip())
        lesson.lesson_type = request.POST.get('lesson_type', 'lecture')
        lesson.practice_mode = request.POST.get('practice_mode', 'code')
        lesson.section_id = request.POST.get('section') or None
        lesson.order = int(request.POST.get('order', '0') or 0)
        lesson.practice_code_template = request.POST.get('practice_code_template', '').strip()
        lesson.practice_task = request.POST.get('practice_task', '').strip()
        test_cases_raw = request.POST.get('test_cases', '').strip()
        lesson.control_time_limit_minutes = int(request.POST.get('control_time_limit_minutes', '30') or 30)
        control_questions_raw = request.POST.get('control_questions_json', '').strip()

        is_it = True if lesson.course.category is None else bool(getattr(lesson.course.category, 'is_it', False))
        posted_testcases = bool(request.POST.getlist('testcase_input') or request.POST.getlist('testcase_output'))
        if lesson.lesson_type == 'control':
            lesson.practice_mode = 'quiz'
        elif lesson.lesson_type == 'practice':
            if posted_testcases:
                lesson.practice_mode = 'code'
            elif not is_it:
                lesson.practice_mode = 'quiz'

        if lesson.lesson_type == 'practice':
            new_test_cases = []
            if test_cases_raw:
                try:
                    new_test_cases = json.loads(test_cases_raw)
                except json.JSONDecodeError:
                    new_test_cases = []
            if not new_test_cases:
                inputs = request.POST.getlist('testcase_input')
                outputs = request.POST.getlist('testcase_output')
                new_test_cases = [
                    {'input': inp, 'output': out}
                    for inp, out in zip(inputs, outputs)
                    if (inp or out)
                ]
            if lesson.practice_mode != 'code':
                new_test_cases = []
            lesson.test_cases = new_test_cases
            # Debug logging for practice test saves
            try:
                debug_path = settings.BASE_DIR / 'practice_save_debug.log'
                with open(debug_path, 'a', encoding='utf-8') as f:
                    f.write(f"[EDIT] lesson_id={lesson.id} lesson_type={lesson.lesson_type} practice_mode={lesson.practice_mode} "
                            f"is_it={is_it} posted_testcases={posted_testcases} raw_len={len(test_cases_raw)} "
                            f"parsed_count={len(new_test_cases)} inputs={len(request.POST.getlist('testcase_input'))} "
                            f"outputs={len(request.POST.getlist('testcase_output'))}\n")
            except Exception:
                pass
        else:
            lesson.practice_code_template = ''
            lesson.practice_task = ''
            lesson.test_cases = []
        lesson.control_pass_threshold = int(request.POST.get('control_pass_threshold', '70') or 70)
        lesson.control_lock_minutes = int(request.POST.get('control_lock_minutes', '10') or 10)
        lesson.save()
        _create_attachments_from_request(request, lesson)

        if lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz'):
            from .models import ControlQuestion, ControlQuestionOption
            ControlQuestionOption.objects.filter(question__lesson=lesson).delete()
            ControlQuestion.objects.filter(lesson=lesson).delete()
            if control_questions_raw:
                try:
                    questions_payload = json.loads(control_questions_raw)
                except json.JSONDecodeError:
                    questions_payload = []
                for q_index, q in enumerate(questions_payload, start=1):
                    question_kind = q.get('question_kind', 'theory')
                    if lesson.lesson_type == 'practice':
                        question_kind = 'theory'
                    question = ControlQuestion.objects.create(
                        lesson=lesson,
                        prompt=q.get('prompt', ''),
                        question_type=q.get('question_type', 'single'),
                        question_kind=question_kind,
                        practice_input=q.get('practice_input', ''),
                        practice_output=q.get('practice_output', ''),
                        order=q_index,
                        weight=int(q.get('weight') or 1),
                        min_words=int(q.get('min_words') or 20),
                        required_keywords=q.get('required_keywords') or [],
                    )
                    options = q.get('options') or []
                    for o_index, opt in enumerate(options, start=1):
                        ControlQuestionOption.objects.create(
                            question=question,
                            option_text=opt.get('option_text', ''),
                            is_correct=bool(opt.get('is_correct')),
                            order=o_index,
                        )

        messages.success(request, 'Урок обновлен.')
        return redirect('creator_lesson_edit', lesson_id=lesson.id)

    sections = CourseSection.objects.filter(course=lesson.course).order_by('order')
    return render(request, 'education/creator_lesson_form.html', {
        'course': lesson.course,
        'sections': sections,
        'lesson': lesson,
        'is_edit': True,
        'is_it_course': True if lesson.course.category is None else bool(getattr(lesson.course.category, 'is_it', False)),
        'control_questions_json': [
            {
                'prompt': q.prompt,
                'question_type': q.question_type,
                'question_kind': q.question_kind,
                'practice_input': q.practice_input,
                'practice_output': q.practice_output,
                'order': q.order,
                'weight': q.weight,
                'min_words': q.min_words,
                'required_keywords': q.required_keywords or [],
                'options': [
                    {
                        'option_text': opt.option_text,
                        'is_correct': opt.is_correct,
                        'order': opt.order,
                    } for opt in q.options.all().order_by('order', 'id')
                ]
            } for q in lesson.control_questions.all().order_by('order', 'id')
        ],
    })


@login_required
@require_POST
def creator_lesson_delete(request, lesson_id):
    from .models import Lesson

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not _can_manage_course(request.user, lesson.course):
        return redirect('creator_courses')
    course_id = lesson.course.id
    lesson.delete()
    messages.success(request, 'Урок удален.')
    return redirect('creator_course_builder', course_id=course_id)


@login_required
@require_http_methods(["GET", "POST"])
def creator_control_question_create(request, lesson_id):
    from .models import Lesson, ControlQuestion

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not _can_manage_course(request.user, lesson.course):
        return redirect('creator_courses')

    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        question_type = request.POST.get('question_type', 'single')
        order = int(request.POST.get('order', '0') or 0)
        weight = int(request.POST.get('weight', '1') or 1)
        min_words = int(request.POST.get('min_words', '20') or 20)
        keywords_raw = request.POST.get('required_keywords', '').strip()
        keywords = [item.strip() for item in keywords_raw.split(',') if item.strip()] if keywords_raw else []
        if not prompt:
            messages.error(request, 'Введите текст вопроса.')
        else:
            ControlQuestion.objects.create(
                lesson=lesson,
                prompt=prompt,
                question_type=question_type,
                order=order,
                weight=weight,
                min_words=min_words,
                required_keywords=keywords,
            )
            messages.success(request, 'Вопрос добавлен.')
            return redirect('creator_lesson_edit', lesson_id=lesson.id)

    return render(request, 'education/creator_question_form.html', {
        'lesson': lesson,
        'is_edit': False,
    })


@login_required
@require_http_methods(["GET", "POST"])
def creator_control_question_edit(request, question_id):
    from .models import ControlQuestion

    question = get_object_or_404(ControlQuestion, id=question_id)
    if not _can_manage_course(request.user, question.lesson.course):
        return redirect('creator_courses')

    if request.method == 'POST':
        question.prompt = request.POST.get('prompt', '').strip()
        question.question_type = request.POST.get('question_type', 'single')
        question.order = int(request.POST.get('order', '0') or 0)
        question.weight = int(request.POST.get('weight', '1') or 1)
        question.min_words = int(request.POST.get('min_words', '20') or 20)
        keywords_raw = request.POST.get('required_keywords', '').strip()
        question.required_keywords = [item.strip() for item in keywords_raw.split(',') if item.strip()] if keywords_raw else []
        question.save()
        messages.success(request, 'Вопрос обновлен.')
        return redirect('creator_lesson_edit', lesson_id=question.lesson.id)

    return render(request, 'education/creator_question_form.html', {
        'lesson': question.lesson,
        'question': question,
        'is_edit': True,
    })


@login_required
@require_POST
def creator_control_question_delete(request, question_id):
    from .models import ControlQuestion

    question = get_object_or_404(ControlQuestion, id=question_id)
    if not _can_manage_course(request.user, question.lesson.course):
        return redirect('creator_courses')
    lesson_id = question.lesson.id
    question.delete()
    messages.success(request, 'Вопрос удален.')
    return redirect('creator_lesson_edit', lesson_id=lesson_id)


@login_required
@require_http_methods(["GET", "POST"])
def creator_control_option_create(request, question_id):
    from .models import ControlQuestion, ControlQuestionOption

    question = get_object_or_404(ControlQuestion, id=question_id)
    if not _can_manage_course(request.user, question.lesson.course):
        return redirect('creator_courses')

    if request.method == 'POST':
        text = request.POST.get('option_text', '').strip()
        is_correct = request.POST.get('is_correct') == 'on'
        order = int(request.POST.get('order', '0') or 0)
        if not text:
            messages.error(request, 'Введите текст варианта.')
        else:
            ControlQuestionOption.objects.create(
                question=question,
                option_text=text,
                is_correct=is_correct,
                order=order,
            )
            messages.success(request, 'Вариант добавлен.')
            return redirect('creator_lesson_edit', lesson_id=question.lesson.id)

    return render(request, 'education/creator_option_form.html', {
        'question': question,
    })


@login_required
@require_POST
def creator_control_option_delete(request, option_id):
    from .models import ControlQuestionOption

    option = get_object_or_404(ControlQuestionOption, id=option_id)
    if not _can_manage_course(request.user, option.question.lesson.course):
        return redirect('creator_courses')
    lesson_id = option.question.lesson.id
    option.delete()
    messages.success(request, 'Вариант удален.')
    return redirect('creator_lesson_edit', lesson_id=lesson_id)


@login_required
@require_POST
def creator_submit_course(request, course_id):
    from .models import Course

    course = get_object_or_404(Course, id=course_id)
    if not _can_manage_course(request.user, course):
        return redirect('creator_courses')

    course.status = 'pending_auto'
    course.auto_reject_reason = ''
    course.moderator_comment = ''
    course.submitted_at = timezone.now()
    course.save(update_fields=['status', 'auto_reject_reason', 'moderator_comment', 'submitted_at'])

    reasons = _scan_course_for_prohibited(course)
    if reasons:
        course.status = 'auto_rejected'
        course.auto_reject_reason = '; '.join(reasons)
        course.save(update_fields=['status', 'auto_reject_reason'])
        messages.error(request, f'Курс отклонен автоматически: {course.auto_reject_reason}')
        return redirect('creator_course_builder', course_id=course.id)

    course.status = 'pending_moderation'
    course.save(update_fields=['status'])
    messages.success(request, 'Курс отправлен на модерацию.')
    return redirect('creator_course_builder', course_id=course.id)


@login_required
def moderator_courses_queue(request):
    from .models import Course

    if not _is_moderator_user(request.user) and not _is_admin_user(request.user):
        return redirect('home')

    courses = Course.objects.filter(status='pending_moderation').select_related('creator').order_by('submitted_at')
    return render(request, 'education/moderator_courses_queue.html', {'courses': courses})


@login_required
@require_http_methods(["GET", "POST"])
def moderator_course_review(request, course_id):
    from .models import Course, CourseModerationLog

    if not _is_moderator_user(request.user) and not _is_admin_user(request.user):
        return redirect('home')

    course = Course.objects.filter(id=course_id).select_related('creator', 'category').prefetch_related(
        'sections__lessons',
        'lessons',
        'lessons__control_questions__options',
    ).first()
    if not course:
        raise Http404('Курс не найден')
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comment = request.POST.get('comment', '').strip()
        if decision == 'approve':
            course.status = 'approved'
            course.is_active = True
            course.approved_at = timezone.now()
            course.moderator_comment = comment
            course.save(update_fields=['status', 'is_active', 'approved_at', 'moderator_comment'])
            CourseModerationLog.objects.create(course=course, moderator=request.user, decision='approved', comment=comment)
            try:
                if course.creator and course.creator.email:
                    send_mail(
                        subject='Ваш курс прошел модерацию',
                        message=(
                            f'Здравствуйте!\n\n'
                            f'Ваш курс "{course.title}" успешно прошел модерацию и опубликован.\n'
                            f'Теперь он доступен для покупки и прохождения.\n\n'
                            f'Спасибо за качественный контент!'
                        ),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[course.creator.email],
                        fail_silently=True,
                    )
            except Exception:
                pass
            messages.success(request, 'Курс опубликован.')
        elif decision == 'reject':
            course.status = 'rejected'
            course.moderator_comment = comment
            course.save(update_fields=['status', 'moderator_comment'])
            CourseModerationLog.objects.create(course=course, moderator=request.user, decision='rejected', comment=comment)
            messages.error(request, 'Курс отклонен.')
        return redirect('moderator_courses_queue')

    return render(request, 'education/moderator_course_review.html', {'course': course})

def course_detail_view(request, course_id):
    """Course detail with sections, access control, and progress"""
    from .models import Course, Lesson, CourseProgress, CourseSection, CourseEnrollment, CourseFavorite, CourseRating

    course = get_object_or_404(Course, id=course_id, is_active=True)
    if not _can_view_course(request.user, course):
        raise Http404("Курс не опубликован")

    enrollment = None
    has_access = False
    user_progress = None
    is_favorite = False
    completed_lessons = set()
    can_favorite_course = request.user.is_authenticated and _is_course_visible_in_catalog(course)
    course_avg_rating = 0.0
    course_rating_count = 0
    user_course_rating = None
    can_rate_course = False

    if request.user.is_authenticated:
        enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
        has_access = _has_course_access(request.user, enrollment)
        is_favorite = CourseFavorite.objects.filter(user=request.user, course=course).exists()
        can_rate_course = bool(enrollment and enrollment.is_paid)
        if can_rate_course:
            user_course_rating = CourseRating.objects.filter(course=course, user=request.user).first()
        if has_access:
            user_progress, _ = CourseProgress.objects.get_or_create(user=request.user, course=course)
            completed_lessons = set(user_progress.completed_lessons.values_list('id', flat=True))

    rating_agg = CourseRating.objects.filter(course=course).aggregate(avg=Avg('rating'), cnt=Count('id'))
    course_avg_rating = round(rating_agg['avg'] or 0, 2)
    course_rating_count = rating_agg['cnt'] or 0

    paid_enrollments_qs = CourseEnrollment.objects.filter(course=course, is_paid=True).exclude(
        Q(user__role__in=ADMIN_ROLES) | Q(user__is_staff=True) | Q(user__is_superuser=True)
    )
    completed_user_ids_qs = CourseProgress.objects.filter(course=course, is_completed=True).values_list('user_id', flat=True)
    active_learners_count = paid_enrollments_qs.exclude(user_id__in=completed_user_ids_qs).values('user_id').distinct().count()

    sections_qs = CourseSection.objects.filter(course=course).prefetch_related('lessons').order_by('order')
    sections = list(sections_qs)
    section_blocks = []
    accessible_lessons = set()

    demo_section_id = sections[0].id if sections else None

    if not sections:
        lessons = list(course.lessons.all().order_by('order'))
        if has_access:
            accessible_lessons = {lesson.id for lesson in lessons}
        section_blocks.append({
            'section': None,
            'lessons': lessons,
            'unlocked': has_access,
            'completed': bool(lessons) and all(lesson.id in completed_lessons for lesson in lessons),
        })
    else:
        previous_control = None
        previous_control_completed = True if has_access else False
        previous_section_obj = None

        for section in sections:
            if has_access:
                if previous_control:
                    previous_control_completed = user_progress and user_progress.completed_lessons.filter(id=previous_control.id).exists()
                    section_unlocked = bool(previous_control_completed)
                elif previous_section_obj:
                    prev_lessons = list(previous_section_obj.lessons.all().order_by('order'))
                    section_unlocked = bool(prev_lessons) and all(l.id in completed_lessons for l in prev_lessons)
                else:
                    section_unlocked = True
            else:
                # Demo mode: only the first block is available until payment.
                section_unlocked = section.id == demo_section_id

            lessons = list(section.lessons.all().order_by('order'))

            if section_unlocked:
                accessible_lessons.update([lesson.id for lesson in lessons])

            control_lesson = next((lesson for lesson in lessons if lesson.lesson_type == 'control'), None)
            section_blocks.append({
                'section': section,
                'lessons': lessons,
                'unlocked': section_unlocked,
                'control_lesson': control_lesson,
                'lock_reason': '' if section_unlocked else 'Откроется после выполнения контрольной работы предшествующего блока',
                'completed': bool(lessons) and all(lesson.id in completed_lessons for lesson in lessons),
            })
            previous_control = control_lesson
            previous_section_obj = section

    context = {
        'course': course,
        'section_blocks': section_blocks,
        'user_progress': user_progress,
        'has_access': has_access,
        'enrollment': enrollment,
        'accessible_lessons': accessible_lessons,
        'demo_section_id': demo_section_id,
        'completed_lessons': completed_lessons,
        'is_favorite': is_favorite,
        'can_favorite_course': can_favorite_course,
        'course_avg_rating': course_avg_rating,
        'course_rating_count': course_rating_count,
        'active_learners_count': active_learners_count,
        'can_rate_course': can_rate_course,
        'user_course_rating': user_course_rating.rating if user_course_rating else 0,
    }
    return render(request, 'education/course_detail.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def purchase_course(request, course_id):
    """Payment flow for regular users, auto-confirm for admins."""
    from .models import Course, CourseEnrollment, Order, PayoutTransaction

    course = get_object_or_404(Course, id=course_id, is_active=True)
    if not _can_view_course(request.user, course):
        raise Http404("Курс не опубликован")
    enrollment, _ = CourseEnrollment.objects.get_or_create(user=request.user, course=course)

    latest_order = Order.objects.filter(user=request.user, course=course, status='paid').order_by('-paid_at', '-created_at').first()

    if request.method == "GET":
        if enrollment.is_paid and not _is_admin_user(request.user):
            if latest_order:
                return redirect('order_detail', order_id=latest_order.id)
            messages.info(request, 'Курс уже оплачен.')
            return redirect('course_detail', course_id=course.id)
        context = {
            "course": course,
            "enrollment": enrollment,
            "is_admin_user": _is_admin_user(request.user),
            "latest_order": latest_order,
            "default_email": request.user.email or "",
        }
        return render(request, "education/payment_page.html", context)

    # Admins can auto-confirm access without payment flow.
    if _is_admin_user(request.user):
        enrollment.is_paid = True
        enrollment.purchased_at = timezone.now()
        enrollment.save(update_fields=['is_paid', 'purchased_at'])
        admin_order = Order.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            status='paid',
            payment_method='admin',
            receipt_email=request.user.email or '',
            paid_at=timezone.now(),
            seller=course.creator,
        )
        admin_order.receipt_number = f"GG-{admin_order.id:06d}"
        admin_order.save(update_fields=['receipt_number'])
        messages.success(request, 'Доступ к курсу подтвержден автоматически (режим администратора).')
        return redirect('order_detail', order_id=admin_order.id)

    if enrollment.is_paid:
        existing_order = Order.objects.filter(user=request.user, course=course, status='paid').order_by('-paid_at', '-created_at').first()
        if existing_order:
            return redirect('order_detail', order_id=existing_order.id)

    payment_method = request.POST.get('payment_method', 'stub').strip() or 'stub'
    email_for_receipt = request.POST.get('email_for_receipt', '').strip() or request.user.email
    billing_name = request.POST.get('billing_name', '').strip()
    billing_phone = request.POST.get('billing_phone', '').strip()

    if not email_for_receipt:
        messages.error(request, 'Укажите email для отправки чека.')
        return redirect('course_purchase', course_id=course.id)

    enrollment.is_paid = True
    enrollment.purchased_at = timezone.now()
    enrollment.save(update_fields=['is_paid', 'purchased_at'])
    commission_amount = (course.price * COMMISSION_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    payout_amount = (course.price - commission_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    order = Order.objects.create(
        user=request.user,
        course=course,
        amount=course.price,
        commission_amount=commission_amount,
        payout_amount=payout_amount,
        seller=course.creator,
        status='paid',
        payment_method=payment_method,
        receipt_email=email_for_receipt,
        billing_name=billing_name or request.user.get_full_name() or request.user.username,
        billing_phone=billing_phone,
        paid_at=timezone.now(),
    )
    order.receipt_number = f"GG-{order.id:06d}"
    order.save(update_fields=['receipt_number'])

    if course.creator:
        PayoutTransaction.objects.create(
            order=order,
            seller=course.creator,
            amount=payout_amount,
            status='pending',
            payout_details=course.payout_details,
        )

    messages.success(request, 'Оплата прошла успешно. Проверьте чек на следующей странице.')
    return redirect('order_detail', order_id=order.id)


@login_required
@require_POST
def send_course_receipt(request, course_id):
    from .models import Course, CourseEnrollment, Order

    course = get_object_or_404(Course, id=course_id, is_active=True)
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment or not enrollment.is_paid:
        messages.error(request, 'Чек можно отправить только после оплаты курса.')
        return redirect('course_purchase', course_id=course.id)

    order = Order.objects.filter(user=request.user, course=course, status='paid').order_by('-paid_at', '-created_at').first()
    email = request.POST.get('email_for_receipt', '').strip() or (order.receipt_email if order else '') or request.user.email
    if not email:
        messages.error(request, 'Укажите email для отправки чека.')
        return redirect('course_purchase', course_id=course.id)

    course_link = request.build_absolute_uri(reverse('course_detail', args=[course.id]))
    subject = f"Чек за курс: {course.title}"
    message = (
        f"Электронный чек\n\n"
        f"Плательщик: {order.billing_name if order else request.user.username}\n"
        f"Телефон: {order.billing_phone if order and order.billing_phone else 'не указан'}\n"
        f"Курс: {course.title}\n"
        f"Сумма: {course.price} ₽\n"
        f"Способ оплаты: {order.payment_method if order else 'stub'}\n"
        f"Дата оплаты: {(order.paid_at or timezone.now()).strftime('%d.%m.%Y %H:%M')}\n"
        f"Номер чека: {order.receipt_number if order else '—'}\n\n"
        f"Ссылка на курс: {course_link}\n"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@coursehub.local',
            [email],
            fail_silently=False,
        )
        messages.success(request, f'Чек отправлен на {email}.')
    except Exception as exc:
        logger.exception('Ошибка отправки чека (course receipt): %s', exc)
        if settings.DEBUG:
            messages.error(request, f'Не удалось отправить чек: {exc}')
        else:
            messages.error(request, 'Не удалось отправить чек. Проверьте настройки почты.')

    return redirect('course_purchase', course_id=course.id)


@login_required
def order_list_view(request):
    from .models import Order

    orders = Order.objects.filter(user=request.user).select_related('course').order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'education/order_list.html', {'page_obj': page_obj})


@login_required
def order_detail_view(request, order_id):
    from .models import Order

    order = get_object_or_404(Order, id=order_id, user=request.user)
    course_link = reverse('course_detail', args=[order.course.id])
    return render(request, 'education/order_detail.html', {
        'order': order,
        'course_link': course_link,
    })


@login_required
@require_POST
def send_order_receipt(request, order_id):
    from .models import Order

    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'paid':
        messages.error(request, 'Чек можно отправить только после оплаты.')
        return redirect('order_detail', order_id=order.id)

    email = request.POST.get('email_for_receipt', '').strip() or order.receipt_email or request.user.email
    if not email:
        messages.error(request, 'Укажите email для отправки чека.')
        return redirect('order_detail', order_id=order.id)

    course_link = request.build_absolute_uri(reverse('course_detail', args=[order.course.id]))
    subject = f"Чек за курс: {order.course.title}"
    message = (
        f"Электронный чек\n\n"
        f"Плательщик: {order.billing_name or request.user.username}\n"
        f"Телефон: {order.billing_phone or 'не указан'}\n"
        f"Курс: {order.course.title}\n"
        f"Сумма: {order.amount} ₽\n"
        f"Способ оплаты: {order.payment_method}\n"
        f"Дата оплаты: {(order.paid_at or timezone.now()).strftime('%d.%m.%Y %H:%M')}\n"
        f"Номер чека: {order.receipt_number or '—'}\n\n"
        f"Ссылка на курс: {course_link}\n"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@coursehub.local',
            [email],
            fail_silently=False,
        )
        messages.success(request, f'Чек отправлен на {email}.')
    except Exception as exc:
        logger.exception('Ошибка отправки чека (order receipt): %s', exc)
        if settings.DEBUG:
            messages.error(request, f'Не удалось отправить чек: {exc}')
        else:
            messages.error(request, 'Не удалось отправить чек. Проверьте настройки почты.')

    return redirect('order_detail', order_id=order.id)

def _finalize_lesson_completion(user, lesson, user_progress):
    from .models import Achievement, UserAchievement, Certificate, UserCertificate

    course = lesson.course
    if user_progress.completed_lessons.filter(id=lesson.id).exists():
        return {
            'already_completed': True,
            'next_lesson_id': None,
            'is_course_completed': user_progress.is_completed,
        }

    user_progress.completed_lessons.add(lesson)
    lessons = list(course.lessons.select_related('section').all().order_by('section__order', 'order', 'id'))
    next_lesson_id = None
    if lesson in lessons:
        current_index = lessons.index(lesson)
        if current_index + 1 < len(lessons):
            next_lesson_id = lessons[current_index + 1].id

    total_lessons = course.lessons.count()
    completed_count = user_progress.completed_lessons.count()
    is_course_completed = False

    if completed_count >= total_lessons and not user_progress.is_completed:
        user_progress.is_completed = True
        user_progress.completed_date = timezone.now()
        user_progress.save()
        is_course_completed = True

        achievement_name = f"Завершен курс: {course.title}"
        achievement, _ = Achievement.objects.get_or_create(
            name=achievement_name,
            defaults={
                'description': f'Вы успешно завершили курс "{course.title}"',
                'criteria': {'course_id': course.id}
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)

        certificate_name = f"Сертификат о прохождении курса: {course.title}"
        certificate, _ = Certificate.objects.get_or_create(
            name=certificate_name,
            defaults={
                'description': f'Сертификат подтверждает успешное прохождение курса "{course.title}"',
                'criteria': {'course_id': course.id}
            }
        )
        user_certificate, _ = UserCertificate.objects.get_or_create(user=user, certificate=certificate)
        if not user_certificate.verification_code:
            user_certificate.save(update_fields=['verification_code'])

    return {
        'already_completed': False,
        'next_lesson_id': next_lesson_id,
        'is_course_completed': is_course_completed,
    }


def _evaluate_control_question(question, request):
    if question.question_type == 'single':
        answer = request.POST.get(f'question_{question.id}', '').strip()
        selected = int(answer) if answer.isdigit() else None
        correct_option = question.options.filter(is_correct=True).first()
        is_correct = bool(correct_option and selected == correct_option.id)
        payload = {'selected': selected}
        return is_correct, payload

    if question.question_type == 'multiple':
        answers = request.POST.getlist(f'question_{question.id}')
        selected = sorted([int(item) for item in answers if item.isdigit()])
        expected = sorted(list(question.options.filter(is_correct=True).values_list('id', flat=True)))
        is_correct = selected == expected
        payload = {'selected': selected}
        return is_correct, payload

    text_answer = request.POST.get(f'question_{question.id}', '').strip()
    words_count = len([w for w in text_answer.split() if w])
    keywords = [str(word).lower() for word in (question.required_keywords or []) if str(word).strip()]
    answer_lower = text_answer.lower()
    hits = sum(1 for word in keywords if word in answer_lower)

    if keywords:
        threshold_hits = max(1, int(len(keywords) * 0.6))
        is_correct = words_count >= question.min_words and hits >= threshold_hits
    else:
        is_correct = words_count >= question.min_words

    payload = {
        'text': text_answer,
        'words_count': words_count,
        'keyword_hits': hits,
    }
    return is_correct, payload


def _get_control_question_order(lesson):
    from .models import ControlQuestion
    return list(ControlQuestion.objects.filter(lesson=lesson).order_by('order', 'id'))


def _is_empty_control_answer(question, request):
    if question.question_type == 'single':
        return not request.POST.get(f'question_{question.id}', '').strip()
    if question.question_type == 'multiple':
        return len(request.POST.getlist(f'question_{question.id}')) == 0
    return not request.POST.get(f'question_{question.id}', '').strip()


def _next_unanswered_after(order_ids, answers, current_id):
    if current_id in order_ids:
        start = order_ids.index(current_id) + 1
    else:
        start = 0
    for qid in order_ids[start:]:
        if str(qid) not in answers:
            return qid
    return None


def _next_skipped_after(order_ids, skipped_ids, current_id):
    if current_id in order_ids:
        start = order_ids.index(current_id) + 1
    else:
        start = 0
    for qid in order_ids[start:]:
        if qid in skipped_ids:
            return qid
    return None


def _finalize_control_attempt(request, lesson, session, force_fail=False):
    from .models import ControlQuestion, ControlAttempt, ControlLock, CourseProgress

    questions = list(ControlQuestion.objects.filter(lesson=lesson).order_by('order', 'id'))
    if not questions:
        messages.error(request, 'Контрольная пока не настроена преподавателем.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    max_score = 0
    score = 0
    for question in questions:
        max_score += question.weight
        payload = session.answers.get(str(question.id))
        if payload and payload.get('is_correct'):
            score += question.weight

    percent = int((score / max_score) * 100) if max_score else 0
    passed = percent >= lesson.control_pass_threshold and not force_fail

    attempt_answers = dict(session.answers or {})
    if session.skipped:
        attempt_answers['_skipped'] = session.skipped

    ControlAttempt.objects.create(
        user=request.user,
        lesson=lesson,
        score=score,
        max_score=max_score,
        percent=percent,
        passed=passed,
        answers=attempt_answers,
    )

    lock_state, _ = ControlLock.objects.get_or_create(user=request.user, lesson=lesson)
    now = timezone.now()

    if passed:
        lock_state.locked_until = None
        lock_state.last_score = percent
        lock_state.save(update_fields=['locked_until', 'last_score', 'updated_date'])
        user_progress, _ = CourseProgress.objects.get_or_create(user=request.user, course=lesson.course)
        completion_result = _finalize_lesson_completion(request.user, lesson, user_progress)
        session.delete()
        messages.success(request, f'Контрольная успешно пройдена: {percent}%.')
        if completion_result['next_lesson_id']:
            return redirect('lesson_detail', lesson_id=completion_result['next_lesson_id'])
        return redirect('lesson_detail', lesson_id=lesson.id)

    lock_state.failed_attempts += 1
    lock_state.last_score = percent
    lock_state.locked_until = now + timedelta(minutes=lesson.control_lock_minutes)
    lock_state.save(update_fields=['failed_attempts', 'last_score', 'locked_until', 'updated_date'])
    session.delete()
    if force_fail:
        messages.error(request, 'Контрольная не пройдена: были пропущенные вопросы.')
    else:
        messages.error(request, f'Недостаточный результат: {percent}%. Контрольная закрыта на {lesson.control_lock_minutes} минут.')
    return redirect('lesson_detail', lesson_id=lesson.id)


@login_required
def control_test_start(request, lesson_id):
    from .models import Lesson, CourseSection, CourseEnrollment, ControlSession, ControlLock

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not (lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz')):
        messages.error(request, 'Этот урок не является тестовой работой.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    course = lesson.course
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    has_full_access = _has_course_access(request.user, enrollment)
    demo_section = CourseSection.objects.filter(course=course).order_by('order').first()

    if not has_full_access and (not demo_section or lesson.section_id != demo_section.id):
        messages.error(request, 'До оплаты доступен только первый демо-блок курса.')
        return redirect('course_detail', course_id=course.id)

    lock_state = ControlLock.objects.filter(user=request.user, lesson=lesson).first()
    if lock_state and lock_state.locked_until and lock_state.locked_until > timezone.now():
        messages.error(request, 'Контрольная временно заблокирована. Попробуйте позже.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    questions = _get_control_question_order(lesson)
    if not questions:
        messages.error(request, 'Контрольная пока не настроена преподавателем.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    session, _ = ControlSession.objects.get_or_create(user=request.user, lesson=lesson)
    if session.status != 'in_progress' or not session.question_order:
        session.status = 'in_progress'
        session.phase = 'initial'
        session.question_order = [q.id for q in questions]
        session.answers = {}
        session.skipped = []
        session.time_limit_seconds = int(lesson.control_time_limit_minutes) * 60
        session.expires_at = timezone.now() + timedelta(seconds=session.time_limit_seconds)
        session.save()

    first_unanswered = None
    for qid in session.question_order:
        if str(qid) not in (session.answers or {}):
            first_unanswered = qid
            break

    if not first_unanswered:
        return redirect('control_test_summary', lesson_id=lesson.id)
    return redirect('control_test_question', lesson_id=lesson.id, question_id=first_unanswered or session.question_order[0])


@login_required
@require_http_methods(["GET", "POST"])
def control_test_question(request, lesson_id, question_id):
    from .models import Lesson, CourseSection, CourseEnrollment, ControlQuestion, ControlSession, ControlLock

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not (lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz')):
        messages.error(request, 'Этот урок не является тестовой работой.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    course = lesson.course
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    has_full_access = _has_course_access(request.user, enrollment)
    demo_section = CourseSection.objects.filter(course=course).order_by('order').first()

    if not has_full_access and (not demo_section or lesson.section_id != demo_section.id):
        messages.error(request, 'До оплаты доступен только первый демо-блок курса.')
        return redirect('course_detail', course_id=course.id)

    lock_state = ControlLock.objects.filter(user=request.user, lesson=lesson).first()
    if lock_state and lock_state.locked_until and lock_state.locked_until > timezone.now():
        messages.error(request, 'Контрольная временно заблокирована. Попробуйте позже.')
        return redirect('lesson_detail', lesson_id=lesson.id)

    session = ControlSession.objects.filter(user=request.user, lesson=lesson).first()
    if not session or session.status != 'in_progress':
        return redirect('control_test_start', lesson_id=lesson.id)

    if question_id not in session.question_order:
        raise Http404('Вопрос не найден.')

    question = get_object_or_404(ControlQuestion, id=question_id, lesson=lesson)

    if session.expires_at and session.expires_at <= timezone.now():
        return _finalize_control_attempt(request, lesson, session, force_fail=True)

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')
        if action == 'submit' and _is_empty_control_answer(question, request):
            messages.error(request, 'Сначала выберите или заполните ответ, либо нажмите "Пропустить".')
            return redirect('control_test_question', lesson_id=lesson.id, question_id=question.id)

        skipped = list(session.skipped or [])
        answers = dict(session.answers or {})

        if action == 'skip':
            if question.id not in skipped:
                skipped.append(question.id)
        else:
            is_correct, payload = _evaluate_control_question(question, request)
            payload['is_correct'] = is_correct
            answers[str(question.id)] = payload
            if question.id in skipped:
                skipped.remove(question.id)

        session.answers = answers
        session.skipped = skipped
        session.save(update_fields=['answers', 'skipped', 'updated_at'])

        if session.phase == 'review':
            next_skipped = _next_skipped_after(session.question_order, skipped, question.id)
            if next_skipped:
                return redirect('control_test_question', lesson_id=lesson.id, question_id=next_skipped)
            return _finalize_control_attempt(request, lesson, session, force_fail=bool(skipped))

        next_question = _next_unanswered_after(session.question_order, answers, question.id)
        if next_question:
            return redirect('control_test_question', lesson_id=lesson.id, question_id=next_question)

        if skipped:
            return redirect('control_test_summary', lesson_id=lesson.id)
        return _finalize_control_attempt(request, lesson, session, force_fail=False)

    total_questions = len(session.question_order)
    position = session.question_order.index(question.id) + 1
    existing_answer = session.answers.get(str(question.id), {})

    context = {
        'lesson': lesson,
        'question': question,
        'position': position,
        'total_questions': total_questions,
        'skipped_count': len(session.skipped or []),
        'existing_answer': existing_answer,
        'is_review': session.phase == 'review',
    }
    return render(request, 'education/control_question.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def control_test_summary(request, lesson_id):
    from .models import Lesson, ControlSession

    lesson = get_object_or_404(Lesson, id=lesson_id)
    session = ControlSession.objects.filter(user=request.user, lesson=lesson, status='in_progress').first()
    if not session:
        return redirect('control_test_start', lesson_id=lesson.id)

    if session.expires_at and session.expires_at <= timezone.now():
        return _finalize_control_attempt(request, lesson, session, force_fail=True)

    skipped_ids = list(session.skipped or [])
    if request.method == 'POST':
        decision = request.POST.get('return_to_skipped', 'no')
        if decision == 'yes' and skipped_ids:
            session.phase = 'review'
            session.save(update_fields=['phase', 'updated_at'])
            first_skipped = next((qid for qid in session.question_order if qid in skipped_ids), None)
            if first_skipped:
                return redirect('control_test_question', lesson_id=lesson.id, question_id=first_skipped)
        return _finalize_control_attempt(request, lesson, session, force_fail=bool(skipped_ids))

    return render(request, 'education/control_summary.html', {
        'lesson': lesson,
        'skipped_count': len(skipped_ids),
    })


@login_required
def lesson_detail_view(request, lesson_id):
    """Lesson detail with access checks"""
    from .models import (
        Lesson,
        CourseProgress,
        CourseSection,
        CourseEnrollment,
        ControlQuestion,
        ControlLock,
        ControlAttempt,
        ControlSession,
        ContentAttachment,
    )

    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    has_full_access = _has_course_access(request.user, enrollment)
    demo_section = CourseSection.objects.filter(course=course).order_by('order').first()

    if not has_full_access:
        if not demo_section or lesson.section_id != demo_section.id:
            messages.error(request, 'До оплаты доступен только первый демо-блок курса.')
            return redirect('course_detail', course_id=course.id)

    user_progress, _ = CourseProgress.objects.get_or_create(user=request.user, course=course)

    if has_full_access and lesson.section:
        prev_section = CourseSection.objects.filter(course=course, order__lt=lesson.section.order).order_by('-order').first()
        if prev_section:
            control_lesson = prev_section.lessons.filter(lesson_type='control').order_by('order').first()
            if control_lesson:
                if not user_progress.completed_lessons.filter(id=control_lesson.id).exists():
                    messages.error(request, 'Сначала нужно пройти контрольную работу предыдущего блока.')
                    return redirect('course_detail', course_id=course.id)
            else:
                prev_lessons = list(prev_section.lessons.all().order_by('order'))
                if prev_lessons and not all(user_progress.completed_lessons.filter(id=l.id).exists() for l in prev_lessons):
                    messages.error(request, 'Откроется после выполнения контрольной работы предшествующего блока.')
                    return redirect('course_detail', course_id=course.id)

    is_completed = user_progress.completed_lessons.filter(id=lesson_id).exists()
    lesson.content_html = mark_safe(markdown.markdown(lesson.content, extensions=['fenced_code', 'tables', 'nl2br', 'codehilite']))
    lesson_ct = ContentType.objects.get_for_model(Lesson)
    lesson_attachments = ContentAttachment.objects.filter(content_type=lesson_ct, object_id=lesson.id).order_by('created_at')

    next_lesson = None
    if is_completed:
        lessons = list(course.lessons.select_related('section').all().order_by('section__order', 'order', 'id'))
        current_index = lessons.index(lesson) if lesson in lessons else -1
        if current_index >= 0 and current_index + 1 < len(lessons):
            next_lesson = lessons[current_index + 1]

    control_questions = []
    lock_remaining_seconds = 0
    latest_attempt = None
    control_session = None
    control_questions_count = 0

    is_quiz = lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz')
    if is_quiz:
        control_questions_count = ControlQuestion.objects.filter(lesson=lesson).count()
        lock_state = ControlLock.objects.filter(user=request.user, lesson=lesson).first()
        if lock_state and lock_state.locked_until and lock_state.locked_until > timezone.now():
            lock_remaining_seconds = int((lock_state.locked_until - timezone.now()).total_seconds())
        latest_attempt = ControlAttempt.objects.filter(user=request.user, lesson=lesson).order_by('-created_date').first()
        control_session = ControlSession.objects.filter(user=request.user, lesson=lesson, status='in_progress').first()

    context = {
        'lesson': lesson,
        'course': course,
        'is_completed': is_completed,
        'user_progress': user_progress,
        'next_lesson': next_lesson,
        'control_questions': control_questions,
        'control_questions_count': control_questions_count,
        'lock_remaining_seconds': lock_remaining_seconds,
        'latest_attempt': latest_attempt,
        'control_session': control_session,
        'is_quiz': is_quiz,
        'lesson_attachments': lesson_attachments,
        'practice_languages': PRACTICE_LANGUAGE_OPTIONS,
    }
    return render(request, 'education/lesson_detail.html', context)


@login_required
@require_http_methods(["POST"])
def submit_control_test(request, lesson_id):
    from .models import (
        Lesson,
        CourseProgress,
        CourseSection,
        CourseEnrollment,
        ControlQuestion,
        ControlAttempt,
        ControlLock,
    )

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not (lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz')):
        return JsonResponse({'success': False, 'message': 'Этот урок не является тестовой работой.'}, status=400)

    course = lesson.course
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    has_full_access = _has_course_access(request.user, enrollment)
    demo_section = CourseSection.objects.filter(course=course).order_by('order').first()

    if not has_full_access and (not demo_section or lesson.section_id != demo_section.id):
        return JsonResponse({'success': False, 'message': 'До оплаты доступен только первый демо-блок курса.'}, status=403)

    user_progress, _ = CourseProgress.objects.get_or_create(user=request.user, course=course)
    lock_state, _ = ControlLock.objects.get_or_create(user=request.user, lesson=lesson)
    now = timezone.now()
    if lock_state.locked_until and lock_state.locked_until > now:
        remaining = int((lock_state.locked_until - now).total_seconds())
        return JsonResponse({
            'success': False,
            'locked': True,
            'message': 'Контрольная временно заблокирована. Повторите теорию и попробуйте позже.',
            'remaining_seconds': remaining,
        }, status=429)

    questions = list(ControlQuestion.objects.filter(lesson=lesson).prefetch_related('options').order_by('order', 'id'))
    if not questions:
        return JsonResponse({'success': False, 'message': 'Контрольная пока не настроена преподавателем.'}, status=400)

    max_score = 0
    score = 0
    submitted_answers = {}
    for question in questions:
        max_score += question.weight
        is_correct, payload = _evaluate_control_question(question, request)
        payload['is_correct'] = is_correct
        submitted_answers[str(question.id)] = payload
        if is_correct:
            score += question.weight

    percent = int((score / max_score) * 100) if max_score else 0
    passed = percent >= lesson.control_pass_threshold

    ControlAttempt.objects.create(
        user=request.user,
        lesson=lesson,
        score=score,
        max_score=max_score,
        percent=percent,
        passed=passed,
        answers=submitted_answers,
    )

    if passed:
        lock_state.locked_until = None
        lock_state.last_score = percent
        lock_state.save(update_fields=['locked_until', 'last_score', 'updated_date'])

        completion_result = _finalize_lesson_completion(request.user, lesson, user_progress)
        return JsonResponse({
            'success': True,
            'passed': True,
            'message': 'Контрольная успешно пройдена.',
            'percent': percent,
            'threshold': lesson.control_pass_threshold,
            'progress': user_progress.get_progress_percentage(),
            'next_lesson_id': completion_result['next_lesson_id'],
            'is_course_completed': completion_result['is_course_completed'],
        })

    lock_state.failed_attempts += 1
    lock_state.last_score = percent
    lock_state.locked_until = now + timedelta(minutes=lesson.control_lock_minutes)
    lock_state.save(update_fields=['failed_attempts', 'last_score', 'locked_until', 'updated_date'])

    return JsonResponse({
        'success': False,
        'passed': False,
        'locked': True,
        'message': f'Недостаточный результат. Контрольная закрыта на {lesson.control_lock_minutes} минут, повторите теорию.',
        'percent': percent,
        'threshold': lesson.control_pass_threshold,
        'remaining_seconds': lesson.control_lock_minutes * 60,
    }, status=400)


@login_required
@require_http_methods(["POST"])
def complete_lesson(request, lesson_id):
    """Mark lecture/practice lesson as completed with access checks"""
    from .models import Lesson, CourseProgress, CourseEnrollment, CourseSection

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if lesson.lesson_type == 'control' or (lesson.lesson_type == 'practice' and lesson.practice_mode == 'quiz'):
        return JsonResponse({
            'success': False,
            'message': 'Тест отмечается только после прохождения.'
        }, status=400)
    if lesson.lesson_type == 'practice' and lesson.practice_mode == 'code':
        session_key = f'practice_passed_{lesson.id}'
        if not request.session.get(session_key):
            return JsonResponse({
                'success': False,
                'message': 'Сначала пройдите тесты практики.'
            }, status=400)

    course = lesson.course
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    has_full_access = _has_course_access(request.user, enrollment)
    demo_section = CourseSection.objects.filter(course=course).order_by('order').first()

    if not has_full_access and (not demo_section or lesson.section_id != demo_section.id):
        return JsonResponse({
            'success': False,
            'message': 'До оплаты доступен только первый демо-блок курса.'
        }, status=403)

    user_progress, _ = CourseProgress.objects.get_or_create(user=request.user, course=course)

    if has_full_access and lesson.section:
        prev_section = CourseSection.objects.filter(course=course, order__lt=lesson.section.order).order_by('-order').first()
        if prev_section:
            control_lesson = prev_section.lessons.filter(lesson_type='control').order_by('order').first()
            if control_lesson:
                if not user_progress.completed_lessons.filter(id=control_lesson.id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'Сначала нужно пройти контрольную работу предыдущего блока.'
                    }, status=403)
            else:
                prev_lessons = list(prev_section.lessons.all().order_by('order'))
                if prev_lessons and not all(user_progress.completed_lessons.filter(id=l.id).exists() for l in prev_lessons):
                    return JsonResponse({
                        'success': False,
                        'message': 'Откроется после выполнения контрольной работы предшествующего блока.'
                    }, status=403)

    completion_result = _finalize_lesson_completion(request.user, lesson, user_progress)
    if completion_result['already_completed']:
        return JsonResponse({'success': False, 'message': 'Урок уже пройден'})
    if lesson.lesson_type == 'practice' and lesson.practice_mode == 'code':
        request.session.pop(f'practice_passed_{lesson.id}', None)

    return JsonResponse({
        'success': True,
        'message': 'Урок отмечен как пройденный',
        'progress': user_progress.get_progress_percentage(),
        'is_course_completed': completion_result['is_course_completed'],
        'next_lesson_id': completion_result['next_lesson_id'],
    })


@login_required
@require_http_methods(["POST"])
def upload_content_attachment(request):
    from .models import ContentAttachment

    file_obj = request.FILES.get('file')
    external_url = (request.POST.get('external_url') or '').strip()
    title = (request.POST.get('title') or '').strip()

    if not file_obj and not external_url:
        return JsonResponse({'success': False, 'message': 'Передайте файл или ссылку.'}, status=400)

    if external_url:
        parsed = urlparse(external_url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            return JsonResponse({'success': False, 'message': 'Некорректная ссылка.'}, status=400)
        attachment = ContentAttachment.objects.create(
            owner=request.user,
            kind='link',
            title=title or external_url[:120],
            external_url=external_url,
        )
        return JsonResponse({
            'success': True,
            'id': attachment.id,
            'kind': 'link',
            'url': attachment.external_url,
            'title': attachment.title,
        })

    kind = _guess_attachment_kind(file_obj.name)
    attachment = ContentAttachment.objects.create(
        owner=request.user,
        kind=kind,
        title=title or file_obj.name[:255],
        file=file_obj,
    )
    return JsonResponse({
        'success': True,
        'id': attachment.id,
        'kind': kind,
        'url': attachment.file.url,
        'download_url': reverse('attachment_download', kwargs={'attachment_id': attachment.id}) if kind == 'file' else attachment.file.url,
        'title': attachment.title,
    })


@require_http_methods(["GET", "POST"])
def attachment_download(request, attachment_id):
    from .models import ContentAttachment

    attachment = get_object_or_404(ContentAttachment, id=attachment_id)
    if attachment.kind != 'file' or not attachment.file:
        return redirect(attachment.file.url if attachment.file else '/')

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()
        if action == 'download':
            filename = os.path.basename(attachment.file.name) or (attachment.title or 'attachment.bin')
            return FileResponse(attachment.file.open('rb'), as_attachment=True, filename=filename)
        return redirect(request.POST.get('back_url') or request.META.get('HTTP_REFERER') or '/')

    return render(request, 'education/attachment_download_warning.html', {
        'attachment': attachment,
        'back_url': request.META.get('HTTP_REFERER') or '/',
    })


@login_required
def achievements_view(request):
    """Страница достижений пользователя"""
    user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    return render(request, 'achievements_list.html', {'user_achievements': user_achievements})

def _normalize_practice_language(raw_language):
    normalized = str(raw_language or 'python').strip().lower()
    aliases = {
        'py': 'python',
        'python3': 'python',
        'golang': 'go',
        'c++': 'cpp',
        'cxx': 'cpp',
        'cs': 'csharp',
        'c#': 'csharp',
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in PRACTICE_LANGUAGE_MAP else normalized


def _which_any(*binaries):
    for binary in binaries:
        resolved = shutil.which(binary)
        if resolved:
            return resolved
    return None


def _build_language_commands(language, source_path, work_dir):
    import sys

    exe_suffix = '.exe' if os.name == 'nt' else ''
    program_path = os.path.join(work_dir, f'program{exe_suffix}')

    if language == 'python':
        return None, [sys.executable, source_path], None
    if language == 'ruby':
        ruby = _which_any('ruby')
        if not ruby:
            return None, None, 'Ruby не установлен на сервере'
        return None, [ruby, source_path], None
    if language == 'go':
        go = _which_any('go')
        if not go:
            return None, None, 'Go не установлен на сервере'
        return None, [go, 'run', source_path], None
    if language == 'cpp':
        compiler = _which_any('g++', 'clang++')
        if not compiler:
            return None, None, 'Компилятор C++ (g++/clang++) не установлен на сервере'
        compile_cmd = [compiler, source_path, '-O2', '-std=c++17', '-o', program_path]
        return compile_cmd, [program_path], None
    if language == 'csharp':
        csc = _which_any('csc')
        mcs = _which_any('mcs')
        if csc:
            compile_cmd = [csc, '/nologo', f'/out:{program_path}', source_path]
            return compile_cmd, [program_path], None
        if mcs:
            compile_cmd = [mcs, '-nologo', f'-out:{program_path}', source_path]
            if os.name == 'nt':
                return compile_cmd, [program_path], None
            mono = _which_any('mono')
            if not mono:
                return None, None, 'Для запуска C# на сервере нужен mono'
            return compile_cmd, [mono, program_path], None
        return None, None, 'Компилятор C# (csc/mcs) не установлен на сервере'
    if language == 'javascript':
        node = _which_any('node')
        if not node:
            return None, None, 'Node.js не установлен на сервере'
        return None, [node, source_path], None
    if language == 'java':
        javac = _which_any('javac')
        java = _which_any('java')
        if not javac or not java:
            return None, None, 'Java (javac/java) не установлена на сервере'
        class_name = 'Main'
        main_source = os.path.join(work_dir, f'{class_name}.java')
        if source_path != main_source:
            with open(source_path, 'r', encoding='utf-8') as src, open(main_source, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        compile_cmd = [javac, main_source]
        run_cmd = [java, '-cp', work_dir, class_name]
        return compile_cmd, run_cmd, None
    if language == 'php':
        php = _which_any('php')
        if not php:
            return None, None, 'PHP не установлен на сервере'
        return None, [php, source_path], None
    if language == 'rust':
        rustc = _which_any('rustc')
        if not rustc:
            return None, None, 'Rust (rustc) не установлен на сервере'
        compile_cmd = [rustc, source_path, '-O', '-o', program_path]
        return compile_cmd, [program_path], None

    return None, None, 'Неподдерживаемый язык'


def _execute_user_code(language, code, stdin_text='', run_timeout=5):
    import subprocess
    import tempfile

    lang_meta = PRACTICE_LANGUAGE_MAP.get(language)
    if not lang_meta:
        return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': 'Неподдерживаемый язык'}

    with tempfile.TemporaryDirectory() as work_dir:
        source_path = os.path.join(work_dir, f'main{lang_meta["file_ext"]}')
        with open(source_path, 'w', encoding='utf-8') as source_file:
            source_file.write(code)

        compile_cmd, run_cmd, command_error = _build_language_commands(language, source_path, work_dir)
        if command_error:
            return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': command_error}

        if compile_cmd:
            try:
                compile_result = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=15,
                    cwd=work_dir,
                )
            except subprocess.TimeoutExpired:
                return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': 'Превышено время компиляции (максимум 15 секунд)'}
            except Exception as exc:
                return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': f'Ошибка компиляции: {exc}'}

            if compile_result.returncode != 0:
                return {
                    'ok': False,
                    'returncode': compile_result.returncode,
                    'stdout': compile_result.stdout.strip(),
                    'stderr': compile_result.stderr.strip() or 'Ошибка компиляции',
                }

        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        try:
            run_result = subprocess.run(
                run_cmd,
                input=stdin_text or '',
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=run_timeout,
                cwd=work_dir,
                env=env,
            )
            return {
                'ok': run_result.returncode == 0,
                'returncode': run_result.returncode,
                'stdout': run_result.stdout.strip(),
                'stderr': run_result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': 'Превышено время выполнения (максимум 5 секунд)'}
        except Exception as exc:
            return {'ok': False, 'returncode': 1, 'stdout': '', 'stderr': f'Ошибка запуска: {exc}'}


@login_required
@require_http_methods(["POST"])
def run_python_code(request):
    """Выполнение пользовательского кода на сервере с проверкой на тестовых случаях."""
    from .models import Lesson
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        lesson_id = data.get('lesson_id', None)
        language = _normalize_practice_language(data.get('language', 'python'))
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Код не предоставлен'
            })

        if language not in PRACTICE_LANGUAGE_MAP:
            return JsonResponse({
                'success': False,
                'error': f'Язык "{language}" не поддерживается',
                'available_languages': [item['id'] for item in PRACTICE_LANGUAGE_OPTIONS],
            })
        
        # Получаем урок, если указан lesson_id
        lesson = None
        test_cases = []
        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                # Получаем тестовые случаи из нового поля test_cases
                if lesson.test_cases and isinstance(lesson.test_cases, list):
                    test_cases = lesson.test_cases
                # Поддержка старого формата для обратной совместимости
                elif hasattr(lesson, 'test_input') and lesson.test_input and hasattr(lesson, 'test_output') and lesson.test_output:
                    test_cases = [{
                        'input': lesson.test_input,
                        'output': lesson.test_output
                    }]
            except Lesson.DoesNotExist:
                pass
        
        # Если нет тестовых случаев, просто выполняем код без проверки
        if not test_cases:
            execution = _execute_user_code(language, code, stdin_text='')
            if not execution['ok']:
                return JsonResponse({
                    'success': False,
                    'error': execution['stderr'] or 'Ошибка выполнения кода',
                    'output': execution['stdout'],
                })
            return JsonResponse({
                'success': True,
                'output': execution['stdout'],
            })
        
        # Выполняем код для каждого тестового случая
        test_results = []
        all_passed = True
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get('input', '')
            expected_output = test_case.get('output', '')

            execution = _execute_user_code(language, code, stdin_text=test_input)
            actual_output = execution['stdout']
            error = execution['stderr']

            test_passed = False
            if execution['ok']:
                expected_output_stripped = str(expected_output).strip()
                actual_output_stripped = actual_output.strip()
                test_passed = (actual_output_stripped == expected_output_stripped)
            else:
                error = error or 'Ошибка выполнения кода'

            test_results.append({
                'test_number': i + 1,
                'input': test_input,
                'expected': expected_output,
                'actual': actual_output,
                'passed': test_passed,
                'error': error if not test_passed and error else None
            })

            if not test_passed:
                all_passed = False
        
        # Формируем ответ
        passed_count = sum(1 for tr in test_results if tr['passed'])
        total_count = len(test_results)
        
        response_data = {
            'success': True,
            'all_passed': all_passed,
            'passed_count': passed_count,
            'total_count': total_count,
            'test_results': test_results
        }
        
        if all_passed:
            response_data['message'] = f'✓ Все тесты пройдены! ({passed_count}/{total_count})'
        else:
            response_data['message'] = f'✗ Пройдено тестов: {passed_count}/{total_count}. Проверьте решение.'

        if lesson:
            session_key = f'practice_passed_{lesson.id}'
            if all_passed:
                request.session[session_key] = True
            else:
                request.session.pop(session_key, None)
        
        return JsonResponse(response_data)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        })


@login_required
def download_certificate_pdf(request, certificate_id):
    """Generate and download branded certificate PDF with verification QR."""
    user_certificate = get_object_or_404(UserCertificate, id=certificate_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{user_certificate.id}.pdf"'

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    verify_url = request.build_absolute_uri(
        reverse('certificate_verify', args=[user_certificate.verification_code])
    )
    cert_number = f"PCH-{user_certificate.id:06d}"

    # Use a Unicode font so Cyrillic text is rendered correctly in PDF.
    regular_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    font_candidates = [
        (
            "PCH-Regular",
            "PCH-Bold",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
        ),
        (
            "PCH-Regular",
            "PCH-Bold",
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\tahomabd.ttf",
        ),
    ]
    for reg_name, b_name, reg_path, b_path in font_candidates:
        try:
            if reg_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(reg_name, reg_path))
            if b_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(b_name, b_path))
            regular_font = reg_name
            bold_font = b_name
            break
        except Exception:
            continue

    # frame
    margin = 28
    p.setStrokeColor(colors.HexColor("#1f7a8c"))
    p.setLineWidth(2)
    p.roundRect(margin, margin, width - margin * 2, height - margin * 2, 18)

    # Header
    p.setFillColor(colors.HexColor("#1b2a4e"))
    p.rect(margin + 6, height - 95, width - (margin + 6) * 2, 58, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont(bold_font, 14)
    p.drawString(margin + 20, height - 60, "Plekhanov CourseHub")
    p.setFont(regular_font, 10)
    p.drawString(margin + 20, height - 76, "Сертификат подтверждения прохождения курса")

    # Title
    p.setFillColor(colors.HexColor("#1a1f2b"))
    p.setFont(bold_font, 30)
    p.drawCentredString(width / 2, height - 150, "СЕРТИФИКАТ")
    p.setFont(regular_font, 15)
    p.drawCentredString(width / 2, height - 172, "о завершении образовательной программы")

    # Body
    p.setFont(regular_font, 13)
    p.drawCentredString(width / 2, height - 220, "Настоящим подтверждается, что")
    p.setFont(bold_font, 24)
    p.drawCentredString(width / 2, height - 255, user_certificate.user.username)
    p.setFont(regular_font, 13)
    p.drawCentredString(width / 2, height - 285, "успешно завершил(а) курс")
    p.setFont(bold_font, 18)
    p.drawCentredString(width / 2, height - 315, user_certificate.certificate.name[:95])

    description = (user_certificate.certificate.description or "").strip()
    if description:
        p.setFont(regular_font, 11)
        text_obj = p.beginText(margin + 36, height - 350)
        text_obj.setFillColor(colors.HexColor("#5b6375"))
        line_len = 95
        while len(description) > line_len:
            split_index = description.rfind(' ', 0, line_len)
            if split_index == -1:
                split_index = line_len
            text_obj.textLine(description[:split_index])
            description = description[split_index:].strip()
        if description:
            text_obj.textLine(description)
        p.drawText(text_obj)

    # Metadata
    p.setFont(regular_font, 11)
    p.setFillColor(colors.HexColor("#1a1f2b"))
    p.drawString(margin + 22, 140, f"Дата выдачи: {user_certificate.awarded_date.strftime('%d.%m.%Y')}")
    p.drawString(margin + 22, 122, f"Номер сертификата: {cert_number}")
    p.drawString(margin + 22, 104, f"Код верификации: {user_certificate.verification_code}")

    # QR with verification url
    qr_widget = qr.QrCodeWidget(verify_url)
    bounds = qr_widget.getBounds()
    qr_size = 110
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    drawing.add(qr_widget)
    renderPDF.draw(drawing, p, width - margin - qr_size - 20, 92)
    p.setFont(regular_font, 9)
    p.setFillColor(colors.HexColor("#5b6375"))
    p.drawRightString(width - margin - 20, 84, "Сканируйте QR для проверки")

    # Footer
    p.setStrokeColor(colors.HexColor("#d6dce7"))
    p.setLineWidth(1)
    p.line(margin + 20, 76, width - margin - 20, 76)
    p.setFont(regular_font, 9)
    p.setFillColor(colors.HexColor("#5b6375"))
    p.drawString(margin + 22, 62, "Подлинность сертификата проверяется по коду или QR-ссылке.")
    p.drawString(margin + 22, 48, verify_url[:95])

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
