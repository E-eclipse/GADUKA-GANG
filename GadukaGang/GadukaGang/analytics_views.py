"""
Views для аналитического дашборда
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from datetime import datetime, timedelta
from GadukaGang.models import User, Topic, Post, Section, Tag
from GadukaGang.db_procedures import DatabaseViews, DatabaseProcedures
import csv
import json


@staff_member_required
def analytics_dashboard(request):
    """Главная страница аналитического дашборда"""
    
    # Получаем фильтры из GET параметров
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Устанавливаем даты по умолчанию (последние 30 дней)
    if not date_to:
        date_to = datetime.now()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    
    if not date_from:
        date_from = date_to - timedelta(days=30)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    
    # Общая статистика
    stats = {
        'total_users': User.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_posts': Post.objects.filter(is_deleted=False).count(),
        'total_sections': Section.objects.count(),
        'active_users_24h': len(DatabaseViews.get_active_users_24h()),
    }
    
    context = {
        'stats': stats,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'analytics_dashboard.html', context)


@staff_member_required
def analytics_api_data(request):
    """API endpoint для получения данных графиков"""
    
    chart_type = request.GET.get('type', 'daily_activity')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Парсим даты
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    else:
        date_to = datetime.now()
    
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    else:
        date_from = date_to - timedelta(days=30)
    
    data = {}
    
    if chart_type == 'daily_activity':
        # Активность по дням
        activity = DatabaseViews.get_daily_activity(days=30)
        data = {
            'labels': [str(item['activity_date']) for item in activity],
            'datasets': [
                {
                    'label': 'Новые пользователи',
                    'data': [item['new_users'] for item in activity],
                    'borderColor': 'rgba(0, 255, 65, 1)',
                    'backgroundColor': 'rgba(0, 255, 65, 0.1)',
                },
                {
                    'label': 'Новые темы',
                    'data': [item['new_topics'] for item in activity],
                    'borderColor': 'rgba(100, 200, 255, 1)',
                    'backgroundColor': 'rgba(100, 200, 255, 0.1)',
                },
                {
                    'label': 'Новые посты',
                    'data': [item['new_posts'] for item in activity],
                    'borderColor': 'rgba(255, 200, 100, 1)',
                    'backgroundColor': 'rgba(255, 200, 100, 0.1)',
                }
            ]
        }
    
    elif chart_type == 'sections_distribution':
        # Распределение по разделам
        sections = DatabaseViews.get_section_statistics()
        data = {
            'labels': [s['name'] for s in sections[:10]],  # Топ 10
            'datasets': [{
                'data': [s['topics_count'] for s in sections[:10]],
                'backgroundColor': [
                    f'rgba({i*25}, {255-i*20}, {100+i*15}, 0.8)' 
                    for i in range(10)
                ],
            }]
        }
    
    elif chart_type == 'top_contributors':
        # Топ авторов
        contributors = DatabaseViews.get_top_contributors(limit=10)
        data = {
            'labels': [c['username'] for c in contributors],
            'datasets': [{
                'label': 'Количество постов',
                'data': [c['post_count'] for c in contributors],
                'backgroundColor': 'rgba(0, 255, 65, 0.7)',
                'borderColor': 'rgba(0, 255, 65, 1)',
                'borderWidth': 1
            }]
        }
    
    elif chart_type == 'popular_tags':
        # Популярные теги
        tags = DatabaseViews.get_popular_tags(limit=10)
        data = {
            'labels': [t['name'] for t in tags],
            'datasets': [{
                'data': [t['topics_count'] for t in tags],
                'backgroundColor': [
                    f'rgba({100+i*15}, {200-i*10}, {150+i*10}, 0.8)' 
                    for i in range(len(tags))
                ],
            }]
        }
    
    elif chart_type == 'user_roles':
        # Распределение по ролям
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
        # Аналитический отчёт
        report = DatabaseProcedures.generate_analytics_report(date_from, date_to)
        data = {
            'labels': [r['metric_name'] for r in report],
            'datasets': [
                {
                    'label': 'Значение',
                    'data': [r['metric_value'] for r in report],
                    'backgroundColor': 'rgba(0, 255, 65, 0.7)',
                    'borderColor': 'rgba(0, 255, 65, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Изменение (%)',
                    'data': [r['metric_change_percent'] for r in report],
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
    """Экспорт аналитики в CSV"""
    
    export_type = request.GET.get('type', 'daily_activity')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')  # BOM для корректного отображения кириллицы в Excel
    
    writer = csv.writer(response)
    
    if export_type == 'daily_activity':
        activity = DatabaseViews.get_daily_activity(days=30)
        writer.writerow(['Дата', 'Новые пользователи', 'Новые темы', 'Новые посты', 'Активные пользователи'])
        for item in activity:
            writer.writerow([
                item['activity_date'],
                item['new_users'],
                item['new_topics'],
                item['new_posts'],
                item['active_users']
            ])
    
    elif export_type == 'top_contributors':
        contributors = DatabaseViews.get_top_contributors(limit=50)
        writer.writerow(['Пользователь', 'Роль', 'Постов', 'Тем', 'Лайков', 'Дизлайков', 'Достижений', 'Ранг'])
        for c in contributors:
            writer.writerow([
                c['username'],
                c['role'],
                c['post_count'],
                c['topics_count'],
                c['total_likes'],
                c['total_dislikes'],
                c['achievements_count'],
                c['rank_name'] or 'Нет ранга'
            ])
    
    elif export_type == 'sections':
        sections = DatabaseViews.get_section_statistics()
        writer.writerow(['Раздел', 'Тем', 'Постов', 'Авторов', 'Средний рейтинг', 'Последняя активность'])
        for s in sections:
            writer.writerow([
                s['name'],
                s['topics_count'],
                s['posts_count'],
                s['unique_authors'],
                round(s['avg_topic_rating'], 2) if s['avg_topic_rating'] else 0,
                s['last_post_date']
            ])
    
    elif export_type == 'tags':
        tags = DatabaseViews.get_popular_tags(limit=100)
        writer.writerow(['Тег', 'Тем', 'Авторов', 'Просмотров', 'Средний рейтинг'])
        for t in tags:
            writer.writerow([
                t['name'],
                t['topics_count'],
                t['unique_authors'],
                t['total_views'],
                round(t['avg_rating'], 2) if t['avg_rating'] else 0
            ])
    
    elif export_type == 'users':
        users = DatabaseViews.get_user_statistics(limit=1000)
        writer.writerow(['Пользователь', 'Email', 'Роль', 'Постов', 'Тем', 'Достижений', 'Ранг', 'Дата регистрации'])
        for u in users:
            writer.writerow([
                u['username'],
                u['email'],
                u['role'],
                u['post_count'],
                u['topics_created'],
                u['achievements_count'],
                u['rank_name'] or 'Нет ранга',
                u['registration_date']
            ])
    
    return response
