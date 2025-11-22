"""
Django management команда для вызова хранимых процедур
"""
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Вызывает хранимые процедуры базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'procedure',
            type=str,
            choices=[
                'calculate_user_statistics',
                'batch_update_topic_ratings',
                'archive_old_posts',
                'generate_analytics_report',
                'award_achievements_batch',
                'update_user_ranks'
            ],
            help='Имя процедуры для вызова'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя (для calculate_user_statistics)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Количество дней (для archive_old_posts)'
        )
        parser.add_argument(
            '--date-from',
            type=str,
            help='Дата начала (YYYY-MM-DD) для generate_analytics_report'
        )
        parser.add_argument(
            '--date-to',
            type=str,
            help='Дата окончания (YYYY-MM-DD) для generate_analytics_report'
        )

    def handle(self, *args, **options):
        procedure = options['procedure']
        
        with connection.cursor() as cursor:
            try:
                if procedure == 'calculate_user_statistics':
                    user_id = options.get('user_id')
                    if not user_id:
                        self.stdout.write(
                            self.style.ERROR('Требуется указать --user-id')
                        )
                        return
                    
                    cursor.execute(
                        'SELECT * FROM calculate_user_statistics(%s)',
                        [user_id]
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        self.stdout.write(self.style.SUCCESS('\n=== Статистика пользователя ==='))
                        self.stdout.write(f'Всего постов: {result[0]}')
                        self.stdout.write(f'Всего тем: {result[1]}')
                        self.stdout.write(f'Всего лайков: {result[2]}')
                        self.stdout.write(f'Всего дизлайков: {result[3]}')
                        self.stdout.write(f'Карма: {result[4]}')
                        self.stdout.write(f'Достижений: {result[5]}')
                        self.stdout.write(f'Ранг: {result[6]}')
                        self.stdout.write(f'Прогресс ранга: {result[7]}%')
                
                elif procedure == 'batch_update_topic_ratings':
                    cursor.execute('SELECT * FROM batch_update_topic_ratings()')
                    result = cursor.fetchone()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n✓ Обновлено рейтингов: {result[0]}'
                        )
                    )
                    self.stdout.write(f'Время выполнения: {result[1]}')
                
                elif procedure == 'archive_old_posts':
                    days = options['days']
                    cursor.execute(
                        'SELECT * FROM archive_old_posts(%s)',
                        [days]
                    )
                    result = cursor.fetchone()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n✓ Архивировано постов: {result[0]}'
                        )
                    )
                    if result[1]:
                        self.stdout.write(f'Самый старый пост: {result[1]}')
                
                elif procedure == 'generate_analytics_report':
                    date_from = options.get('date_from')
                    date_to = options.get('date_to')
                    
                    if date_from:
                        date_from = datetime.strptime(date_from, '%Y-%m-%d')
                    if date_to:
                        date_to = datetime.strptime(date_to, '%Y-%m-%d')
                    
                    cursor.execute(
                        'SELECT * FROM generate_analytics_report(%s, %s)',
                        [date_from, date_to]
                    )
                    results = cursor.fetchall()
                    
                    self.stdout.write(self.style.SUCCESS('\n=== Аналитический отчёт ==='))
                    for row in results:
                        change_symbol = '↑' if row[2] > 0 else '↓' if row[2] < 0 else '='
                        self.stdout.write(
                            f'{row[0]}: {int(row[1])} ({change_symbol} {abs(row[2]):.1f}%)'
                        )
                
                elif procedure == 'award_achievements_batch':
                    cursor.execute('SELECT * FROM award_achievements_batch()')
                    results = cursor.fetchall()
                    
                    if results:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'\n✓ Выдано достижений: {len(results)}'
                            )
                        )
                        for row in results:
                            self.stdout.write(
                                f'  - Пользователь #{row[0]}: {row[2]}'
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING('Нет новых достижений для выдачи')
                        )
                
                elif procedure == 'update_user_ranks':
                    cursor.execute('SELECT * FROM update_user_ranks()')
                    results = cursor.fetchall()
                    
                    if results:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'\n✓ Обновлено рангов: {len(results)}'
                            )
                        )
                        for row in results:
                            self.stdout.write(
                                f'  - Пользователь #{row[0]}: {row[1]} → {row[2]} ({row[3]} очков)'
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING('Нет пользователей для повышения ранга')
                        )
                
                self.stdout.write(self.style.SUCCESS('\n✓ Процедура выполнена успешно'))
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ Ошибка выполнения процедуры: {str(e)}')
                )
