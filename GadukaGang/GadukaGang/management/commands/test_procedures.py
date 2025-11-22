"""
Скрипт для тестирования хранимых процедур и триггеров
"""
from django.core.management.base import BaseCommand
from django.db import connection
from GadukaGang.db_procedures import DatabaseProcedures, DatabaseViews
from GadukaGang.models import User, Post, Topic, UserProfile
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Тестирует хранимые процедуры и триггеры'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('ТЕСТИРОВАНИЕ ХРАНИМЫХ ПРОЦЕДУР И ТРИГГЕРОВ'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Тест 1: Статистика пользователя
        self.test_user_statistics()
        
        # Тест 2: Пакетное обновление рейтингов
        self.test_batch_update_ratings()
        
        # Тест 3: Генерация аналитического отчёта
        self.test_analytics_report()
        
        # Тест 4: Массовая выдача достижений
        self.test_award_achievements()
        
        # Тест 5: Обновление рангов
        self.test_update_ranks()
        
        # Тест 6: Проверка VIEW
        self.test_views()
        
        # Тест 7: Проверка триггеров
        self.test_triggers()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
    
    def test_user_statistics(self):
        """Тест процедуры calculate_user_statistics"""
        self.stdout.write('\n📊 Тест 1: Статистика пользователя')
        self.stdout.write('-' * 60)
        
        try:
            # Берём первого пользователя
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING('⚠ Нет пользователей для теста'))
                return
            
            stats = DatabaseProcedures.calculate_user_statistics(user.id)
            
            if stats:
                self.stdout.write(self.style.SUCCESS(f'✓ Статистика для {user.username}:'))
                for key, value in stats.items():
                    self.stdout.write(f'  {key}: {value}')
            else:
                self.stdout.write(self.style.ERROR('✗ Не удалось получить статистику'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_batch_update_ratings(self):
        """Тест процедуры batch_update_topic_ratings"""
        self.stdout.write('\n⭐ Тест 2: Пакетное обновление рейтингов')
        self.stdout.write('-' * 60)
        
        try:
            result = DatabaseProcedures.batch_update_topic_ratings()
            self.stdout.write(self.style.SUCCESS(
                f'✓ Обновлено тем: {result["updated_count"]}'
            ))
            self.stdout.write(f'  Время выполнения: {result["execution_time"]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_analytics_report(self):
        """Тест процедуры generate_analytics_report"""
        self.stdout.write('\n📈 Тест 3: Аналитический отчёт')
        self.stdout.write('-' * 60)
        
        try:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=30)
            
            report = DatabaseProcedures.generate_analytics_report(date_from, date_to)
            
            if report:
                self.stdout.write(self.style.SUCCESS('✓ Отчёт сгенерирован:'))
                for metric in report:
                    change = metric['metric_change_percent']
                    symbol = '↑' if change > 0 else '↓' if change < 0 else '='
                    self.stdout.write(
                        f'  {metric["metric_name"]}: {int(metric["metric_value"])} '
                        f'({symbol} {abs(change):.1f}%)'
                    )
            else:
                self.stdout.write(self.style.WARNING('⚠ Отчёт пуст'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_award_achievements(self):
        """Тест процедуры award_achievements_batch"""
        self.stdout.write('\n🏆 Тест 4: Массовая выдача достижений')
        self.stdout.write('-' * 60)
        
        try:
            achievements = DatabaseProcedures.award_achievements_batch()
            
            if achievements:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Выдано достижений: {len(achievements)}'
                ))
                for ach in achievements[:5]:  # Показываем первые 5
                    self.stdout.write(
                        f'  Пользователь #{ach["user_id"]}: {ach["achievement_name"]}'
                    )
            else:
                self.stdout.write(self.style.WARNING('⚠ Нет новых достижений'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_update_ranks(self):
        """Тест процедуры update_user_ranks"""
        self.stdout.write('\n🎖️ Тест 5: Обновление рангов')
        self.stdout.write('-' * 60)
        
        try:
            ranks = DatabaseProcedures.update_user_ranks()
            
            if ranks:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Обновлено рангов: {len(ranks)}'
                ))
                for rank in ranks[:5]:  # Показываем первые 5
                    self.stdout.write(
                        f'  Пользователь #{rank["user_id"]}: '
                        f'{rank["old_rank"]} → {rank["new_rank"]} '
                        f'({rank["current_points"]} очков)'
                    )
            else:
                self.stdout.write(self.style.WARNING('⚠ Нет обновлений рангов'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_views(self):
        """Тест представлений (VIEW)"""
        self.stdout.write('\n👁️ Тест 6: Проверка VIEW')
        self.stdout.write('-' * 60)
        
        try:
            # Тест v_user_statistics
            users = DatabaseViews.get_user_statistics(limit=3)
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_user_statistics: {len(users)} записей'
            ))
            
            # Тест v_topic_statistics
            topics = DatabaseViews.get_topic_statistics(limit=3)
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_topic_statistics: {len(topics)} записей'
            ))
            
            # Тест v_active_users_24h
            active = DatabaseViews.get_active_users_24h()
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_active_users_24h: {len(active)} активных пользователей'
            ))
            
            # Тест v_section_statistics
            sections = DatabaseViews.get_section_statistics()
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_section_statistics: {len(sections)} разделов'
            ))
            
            # Тест v_top_contributors
            contributors = DatabaseViews.get_top_contributors(limit=5)
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_top_contributors: {len(contributors)} авторов'
            ))
            
            # Тест v_daily_activity
            activity = DatabaseViews.get_daily_activity(days=7)
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_daily_activity: {len(activity)} дней'
            ))
            
            # Тест v_popular_tags
            tags = DatabaseViews.get_popular_tags(limit=5)
            self.stdout.write(self.style.SUCCESS(
                f'✓ v_popular_tags: {len(tags)} тегов'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
    
    def test_triggers(self):
        """Тест триггеров"""
        self.stdout.write('\n⚡ Тест 7: Проверка триггеров')
        self.stdout.write('-' * 60)
        
        try:
            # Получаем пользователя для теста
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING('⚠ Нет пользователей для теста'))
                return
            
            # Получаем профиль
            profile, _ = UserProfile.objects.get_or_create(user=user)
            old_post_count = profile.post_count
            
            # Создаём тестовый пост (должен сработать триггер)
            topic = Topic.objects.first()
            if not topic:
                self.stdout.write(self.style.WARNING('⚠ Нет тем для теста'))
                return
            
            test_post = Post.objects.create(
                topic=topic,
                author=user,
                content='Тестовый пост для проверки триггеров'
            )
            
            # Проверяем, что счётчик обновился
            profile.refresh_from_db()
            new_post_count = profile.post_count
            
            if new_post_count > old_post_count:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Триггер update_post_count работает: '
                    f'{old_post_count} → {new_post_count}'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '⚠ Триггер update_post_count не сработал'
                ))
            
            # Удаляем тестовый пост
            test_post.delete()
            
            # Проверяем логи аудита
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT COUNT(*) FROM "GadukaGang_systemlog" '
                    'WHERE timestamp >= NOW() - INTERVAL \'1 minute\''
                )
                log_count = cursor.fetchone()[0]
                
                if log_count > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Триггеры аудита работают: {log_count} записей в логах'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '⚠ Нет записей в логах аудита'
                    ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
