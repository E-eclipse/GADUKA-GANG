"""
Views for analytics dashboard
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Sum, Avg, Max
from datetime import datetime, timedelta
from django.utils import timezone
from GadukaGang.models import (
    User, Topic, Post, Section, Tag, TopicTag, PostLike, TopicRating, UserProfile,
    Course, CourseEnrollment, CourseProgress, Order
)
import csv
import json


@staff_member_required
def analytics_dashboard(request):
    """Main analytics dashboard page"""
    
    # General statistics
    stats = {
        'total_users': User.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_posts': Post.objects.filter(is_deleted=False).count(),
        'total_sections': Section.objects.count(),
        # For SQLite we can't use the database view, so we'll calculate this differently
        'active_users_24h': User.objects.filter(
            userprofile__last_activity__gte=timezone.now() - timedelta(hours=24)
        ).count(),
    }
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'analytics_dashboard.html', context)


@staff_member_required
def analytics_api_data(request):
    """API endpoint for chart data"""
    
    chart_type = request.GET.get('type', 'daily_activity')
    
    data = {}
    
    if chart_type == 'daily_activity':
        # Activity by day (last 30 days)
        activity_data = []
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Users registered on this date
            new_users = User.objects.filter(
                date_joined__date=date.date()
            ).count()
            
            # Topics created on this date
            new_topics = Topic.objects.filter(
                created_date__date=date.date()
            ).count()
            
            # Posts created on this date
            new_posts = Post.objects.filter(
                created_date__date=date.date(),
                is_deleted=False
            ).count()
            
            # Active users on this date
            active_users = User.objects.filter(
                userprofile__last_activity__date=date.date()
            ).count()
            
            activity_data.append({
                'activity_date': date_str,
                'new_users': new_users,
                'new_topics': new_topics,
                'new_posts': new_posts,
                'active_users': active_users
            })
        
        # Reverse to show chronological order
        activity_data.reverse()
        
        data = {
            'labels': [item['activity_date'] for item in activity_data],
            'datasets': [
                {
                    'label': 'New Users',
                    'data': [item['new_users'] for item in activity_data],
                    'borderColor': 'rgba(0, 255, 65, 1)',
                    'backgroundColor': 'rgba(0, 255, 65, 0.1)',
                },
                {
                    'label': 'New Topics',
                    'data': [item['new_topics'] for item in activity_data],
                    'borderColor': 'rgba(100, 200, 255, 1)',
                    'backgroundColor': 'rgba(100, 200, 255, 0.1)',
                },
                {
                    'label': 'New Posts',
                    'data': [item['new_posts'] for item in activity_data],
                    'borderColor': 'rgba(255, 200, 100, 1)',
                    'backgroundColor': 'rgba(255, 200, 100, 0.1)',
                }
            ]
        }
    
    elif chart_type == 'sections_distribution':
        # Distribution by sections
        sections = Section.objects.annotate(
            topics_count=Count('topic')
        ).order_by('-topics_count')[:10]
        
        data = {
            'labels': [s.name for s in sections],
            'datasets': [{
                'data': [s.topics_count for s in sections],
                'backgroundColor': [
                    f'rgba({i*25}, {255-i*20}, {100+i*15}, 0.8)' 
                    for i in range(len(sections))
                ],
            }]
        }
    
    elif chart_type == 'top_contributors':
        # Top contributors
        contributors = User.objects.annotate(
            post_count=Count('post', filter=Q(post__is_deleted=False))
        ).order_by('-post_count')[:10]
        
        data = {
            'labels': [c.username for c in contributors],
            'datasets': [{
                'label': 'Number of Posts',
                'data': [c.post_count for c in contributors],
                'backgroundColor': 'rgba(0, 255, 65, 0.7)',
                'borderColor': 'rgba(0, 255, 65, 1)',
                'borderWidth': 1
            }]
        }
    
    elif chart_type == 'popular_tags':
        # Popular tags
        tags = Tag.objects.annotate(
            topics_count=Count('topic_tags')
        ).order_by('-topics_count')[:10]
        
        data = {
            'labels': [t.name for t in tags],
            'datasets': [{
                'data': [t.topics_count for t in tags],
                'backgroundColor': [
                    f'rgba({100+i*15}, {200-i*10}, {150+i*10}, 0.8)' 
                    for i in range(len(tags))
                ],
            }]
        }
    
    elif chart_type == 'user_roles':
        # Distribution by roles
        roles = User.objects.values('role').annotate(count=Count('id'))
        data = {
            'labels': [r['role'] for r in roles],
            'datasets': [{
                'data': [r['count'] for r in roles],
                'backgroundColor': [
                    'rgba(0, 255, 65, 0.8)',
                    'rgba(100, 200, 255, 0.8)',
                    'rgba(255, 200, 100, 0.8)',
                    'rgba(200, 100, 255, 0.8)',
                    'rgba(255, 100, 100, 0.8)',
                    'rgba(100, 255, 200, 0.8)',
                ],
            }]
        }
    
    elif chart_type == 'analytics_report':
        # Analytics report (simplified version)
        report_data = [
            {
                'metric_name': 'Total Users',
                'metric_value': float(User.objects.count()),
                'metric_change_percent': 0.0
            },
            {
                'metric_name': 'Total Topics',
                'metric_value': float(Topic.objects.count()),
                'metric_change_percent': 0.0
            },
            {
                'metric_name': 'Total Posts',
                'metric_value': float(Post.objects.filter(is_deleted=False).count()),
                'metric_change_percent': 0.0
            },
            {
                'metric_name': 'Active Users (24h)',
                'metric_value': float(User.objects.filter(
                    userprofile__last_activity__gte=timezone.now() - timedelta(hours=24)
                ).count()),
                'metric_change_percent': 0.0
            }
        ]
        
        data = {
            'labels': [r['metric_name'] for r in report_data],
            'datasets': [
                {
                    'label': 'Value',
                    'data': [r['metric_value'] for r in report_data],
                    'backgroundColor': 'rgba(0, 255, 65, 0.7)',
                    'borderColor': 'rgba(0, 255, 65, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Change (%)',
                    'data': [r['metric_change_percent'] for r in report_data],
                    'backgroundColor': 'rgba(255, 200, 100, 0.7)',
                    'borderColor': 'rgba(255, 200, 100, 1)',
                    'borderWidth': 1,
                    'yAxisID': 'y1',
                }
            ]
        }
    
    return JsonResponse(data)


@staff_member_required
def export_analytics_csv(request):
    """Export analytics to CSV"""
    
    export_type = request.GET.get('type', 'daily_activity')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')  # BOM for correct Cyrillic display in Excel
    
    writer = csv.writer(response)
    
    if export_type == 'daily_activity':
        activity_data = []
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            new_users = User.objects.filter(
                date_joined__date=date.date()
            ).count()
            
            new_topics = Topic.objects.filter(
                created_date__date=date.date()
            ).count()
            
            new_posts = Post.objects.filter(
                created_date__date=date.date(),
                is_deleted=False
            ).count()
            
            active_users = User.objects.filter(
                userprofile__last_activity__date=date.date()
            ).count()
            
            activity_data.append({
                'activity_date': date_str,
                'new_users': new_users,
                'new_topics': new_topics,
                'new_posts': new_posts,
                'active_users': active_users
            })
        
        activity_data.reverse()
        
        writer.writerow(['Date', 'New Users', 'New Topics', 'New Posts', 'Active Users'])
        for item in activity_data:
            writer.writerow([
                item['activity_date'],
                item['new_users'],
                item['new_topics'],
                item['new_posts'],
                item['active_users']
            ])
    
    elif export_type == 'top_contributors':
        contributors = User.objects.annotate(
            post_count=Count('post', filter=Q(post__is_deleted=False))
        ).order_by('-post_count')[:50]
        
        writer.writerow(['User', 'Role', 'Posts', 'Topics', 'Likes', 'Dislikes', 'Achievements', 'Rank'])
        for c in contributors:
            # Get additional data
            topics_count = Topic.objects.filter(author=c).count()
            likes_count = PostLike.objects.filter(post__author=c, like_type='like').count()
            dislikes_count = PostLike.objects.filter(post__author=c, like_type='dislike').count()
            achievements_count = c.userachievement_set.count()
            
            try:
                rank_name = c.userprofile.user_rank_progress.rank.name if c.userprofile.user_rank_progress.rank else 'No Rank'
            except:
                rank_name = 'No Rank'
            
            writer.writerow([
                c.username,
                c.role,
                c.post_count,
                topics_count,
                likes_count,
                dislikes_count,
                achievements_count,
                rank_name
            ])
    
    elif export_type == 'sections':
        sections = Section.objects.annotate(
            topics_count=Count('topic'),
            posts_count=Count('topic__post', filter=Q(topic__post__is_deleted=False)),
            unique_authors=Count('topic__author', distinct=True)
        )
        
        writer.writerow(['Section', 'Topics', 'Posts', 'Authors', 'Avg Rating', 'Last Activity'])
        for s in sections:
            # Calculate average rating
            topics_with_ratings = Topic.objects.filter(section=s).exclude(average_rating=0)
            avg_rating = topics_with_ratings.aggregate(avg=Avg('average_rating'))['avg'] or 0
            
            last_activity = Post.objects.filter(
                topic__section=s, 
                is_deleted=False
            ).aggregate(last=Max('created_date'))['last']
            
            writer.writerow([
                s.name,
                s.topics_count,
                s.posts_count,
                s.unique_authors,
                round(avg_rating, 2),
                last_activity.strftime('%Y-%m-%d %H:%M:%S') if last_activity else ''
            ])
    
    elif export_type == 'tags':
        tags = Tag.objects.annotate(
            topics_count=Count('topic_tags'),
            unique_authors=Count('topic_tags__topic__author', distinct=True)
        ).order_by('-topics_count')[:100]
        
        writer.writerow(['Tag', 'Topics', 'Authors', 'Views', 'Avg Rating'])
        for t in tags:
            # Calculate total views and average rating
            topics = Topic.objects.filter(topic_tags__tag=t)
            total_views = topics.aggregate(total=Sum('view_count'))['total'] or 0
            
            topics_with_ratings = topics.exclude(average_rating=0)
            avg_rating = topics_with_ratings.aggregate(avg=Avg('average_rating'))['avg'] or 0
            
            writer.writerow([
                t.name,
                t.topics_count,
                t.unique_authors,
                total_views,
                round(avg_rating, 2)
            ])
    
    elif export_type == 'users':
        users = User.objects.all()[:1000]
        
        writer.writerow(['User', 'Email', 'Role', 'Posts', 'Topics', 'Achievements', 'Rank', 'Registration Date'])
        for u in users:
            # Get additional data
            posts_count = Post.objects.filter(author=u, is_deleted=False).count()
            topics_count = Topic.objects.filter(author=u).count()
            achievements_count = u.userachievement_set.count()
            
            try:
                rank_name = u.userprofile.user_rank_progress.rank.name if u.userprofile.user_rank_progress.rank else 'No Rank'
            except:
                rank_name = 'No Rank'
            
            writer.writerow([
                u.username,
                u.email,
                u.role,
                posts_count,
                topics_count,
                achievements_count,
                rank_name,
                u.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return response


@staff_member_required
def analytics_funnel_api(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    course_filter = Course.objects.all()
    orders_filter = Order.objects.filter(status='paid')
    enroll_filter = CourseEnrollment.objects.filter(is_paid=True)

    if date_from:
        course_filter = course_filter.filter(created_date__date__gte=date_from)
        orders_filter = orders_filter.filter(created_at__date__gte=date_from)
        enroll_filter = enroll_filter.filter(purchased_at__date__gte=date_from)
    if date_to:
        course_filter = course_filter.filter(created_date__date__lte=date_to)
        orders_filter = orders_filter.filter(created_at__date__lte=date_to)
        enroll_filter = enroll_filter.filter(purchased_at__date__lte=date_to)

    catalog = course_filter.count()
    opened = Topic.objects.count()
    purchased = orders_filter.count()
    started = CourseProgress.objects.filter(course__in=course_filter).count()
    completed = CourseProgress.objects.filter(course__in=course_filter, is_completed=True).count()
    return JsonResponse({
        'labels': ['Каталог', 'Интерес', 'Покупка', 'Старт', 'Завершение'],
        'values': [catalog, opened, purchased, started, completed],
    })


@staff_member_required
def analytics_revenue_api(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    qs = Order.objects.filter(status='paid')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    grouped = []
    for i in range(30):
        day = timezone.now().date() - timedelta(days=29 - i)
        day_qs = qs.filter(created_at__date=day)
        grouped.append({
            'day': day.strftime('%Y-%m-%d'),
            'gmv': float(day_qs.aggregate(v=Sum('amount'))['v'] or 0),
            'commission': float(day_qs.aggregate(v=Sum('commission_amount'))['v'] or 0),
            'payout': float(day_qs.aggregate(v=Sum('payout_amount'))['v'] or 0),
        })
    return JsonResponse({
        'labels': [x['day'] for x in grouped],
        'datasets': {
            'gmv': [x['gmv'] for x in grouped],
            'commission': [x['commission'] for x in grouped],
            'payout': [x['payout'] for x in grouped],
        },
    })


@staff_member_required
def analytics_courses_performance_api(request):
    courses = Course.objects.all().order_by('-created_date')[:30]
    labels, started, completed, completion_rate = [], [], [], []
    for c in courses:
        s = CourseProgress.objects.filter(course=c).count()
        cp = CourseProgress.objects.filter(course=c, is_completed=True).count()
        labels.append(c.title)
        started.append(s)
        completed.append(cp)
        completion_rate.append(round((cp / s) * 100, 2) if s else 0)
    return JsonResponse({
        'labels': labels,
        'datasets': {
            'started': started,
            'completed': completed,
            'completion_rate': completion_rate,
        },
    })


@staff_member_required
def analytics_retention_api(request):
    now = timezone.now().date()
    labels, cohorts = [], []
    for offset in range(8):
        cohort_day = now - timedelta(days=(7 - offset) * 7)
        users = User.objects.filter(date_joined__date__gte=cohort_day, date_joined__date__lt=cohort_day + timedelta(days=7))
        base = users.count()
        active_after_week = users.filter(last_login__date__gte=cohort_day + timedelta(days=7)).count()
        labels.append(cohort_day.strftime('%Y-%m-%d'))
        cohorts.append(round((active_after_week / base) * 100, 2) if base else 0)
    dau = User.objects.filter(last_login__date=now).count()
    wau = User.objects.filter(last_login__date__gte=now - timedelta(days=6)).count()
    mau = User.objects.filter(last_login__date__gte=now - timedelta(days=29)).count()
    return JsonResponse({
        'labels': labels,
        'retention': cohorts,
        'dau': dau,
        'wau': wau,
        'mau': mau,
    })
