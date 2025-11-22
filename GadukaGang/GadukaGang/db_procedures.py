"""
Утилиты для работы с хранимыми процедурами PostgreSQL
"""
from django.db import connection
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseProcedures:
    """Класс для вызова хранимых процедур"""
    
    @staticmethod
    def calculate_user_statistics(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Рассчитывает статистику пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь со статистикой или None
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM calculate_user_statistics(%s)',
                    [user_id]
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'total_posts': result[0],
                        'total_topics': result[1],
                        'total_likes': result[2],
                        'total_dislikes': result[3],
                        'achievements_count': result[4],
                        'rank_name': result[5],
                        'rank_progress': result[6]
                    }
                return None
        except Exception as e:
            logger.error(f'Ошибка при расчёте статистики пользователя {user_id}: {e}')
            return None
    
    @staticmethod
    def batch_update_topic_ratings() -> Dict[str, Any]:
        """
        Пакетно обновляет рейтинги всех тем
        
        Returns:
            Словарь с результатами обновления
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM batch_update_topic_ratings()')
                result = cursor.fetchone()
                
                return {
                    'updated_count': result[0],
                    'execution_time': str(result[1])
                }
        except Exception as e:
            logger.error(f'Ошибка при пакетном обновлении рейтингов: {e}')
            return {'updated_count': 0, 'execution_time': '0', 'error': str(e)}
    
    @staticmethod
    def archive_old_posts(days_threshold: int = 365) -> Dict[str, Any]:
        """
        Архивирует старые посты
        
        Args:
            days_threshold: Порог в днях для архивации
            
        Returns:
            Словарь с результатами архивации
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM archive_old_posts(%s)',
                    [days_threshold]
                )
                result = cursor.fetchone()
                
                return {
                    'archived_count': result[0],
                    'oldest_post_date': result[1]
                }
        except Exception as e:
            logger.error(f'Ошибка при архивации постов: {e}')
            return {'archived_count': 0, 'oldest_post_date': None, 'error': str(e)}
    
    @staticmethod
    def generate_analytics_report(
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерирует аналитический отчёт
        
        Args:
            date_from: Дата начала периода
            date_to: Дата окончания периода
            
        Returns:
            Список метрик с изменениями
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM generate_analytics_report(%s, %s)',
                    [date_from, date_to]
                )
                results = cursor.fetchall()
                
                return [
                    {
                        'metric_name': row[0],
                        'metric_value': float(row[1]),
                        'metric_change_percent': float(row[2])
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f'Ошибка при генерации аналитического отчёта: {e}')
            return []
    
    @staticmethod
    def award_achievements_batch() -> List[Dict[str, Any]]:
        """
        Массово выдаёт достижения пользователям
        
        Returns:
            Список выданных достижений
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM award_achievements_batch()')
                results = cursor.fetchall()
                
                return [
                    {
                        'user_id': row[0],
                        'achievement_id': row[1],
                        'achievement_name': row[2]
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f'Ошибка при массовой выдаче достижений: {e}')
            return []
    
    @staticmethod
    def update_user_ranks() -> List[Dict[str, Any]]:
        """
        Обновляет ранги пользователей
        
        Returns:
            Список обновлённых рангов
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM update_user_ranks()')
                results = cursor.fetchall()
                
                return [
                    {
                        'user_id': row[0],
                        'old_rank': row[1],
                        'new_rank': row[2],
                        'current_points': row[3]
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f'Ошибка при обновлении рангов: {e}')
            return []
    
    @staticmethod
    def process_complaint_transaction(
        complaint_id: int,
        moderator_id: int,
        new_status: str,
        action_description: str
    ) -> bool:
        """
        Обрабатывает жалобу с транзакцией
        
        Args:
            complaint_id: ID жалобы
            moderator_id: ID модератора
            new_status: Новый статус
            action_description: Описание действия
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT process_complaint_transaction(%s, %s, %s, %s)',
                    [complaint_id, moderator_id, new_status, action_description]
                )
                result = cursor.fetchone()
                return result[0] if result else False
        except Exception as e:
            logger.error(f'Ошибка при обработке жалобы {complaint_id}: {e}')
            return False


class DatabaseViews:
    """Класс для работы с представлениями (VIEW)"""
    
    @staticmethod
    def get_user_statistics(limit: int = 100) -> List[Dict[str, Any]]:
        """Получает статистику пользователей из VIEW"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM v_user_statistics ORDER BY post_count DESC LIMIT %s',
                    [limit]
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении статистики пользователей: {e}')
            return []
    
    @staticmethod
    def get_topic_statistics(limit: int = 100) -> List[Dict[str, Any]]:
        """Получает статистику тем из VIEW"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM v_topic_statistics ORDER BY posts_count DESC LIMIT %s',
                    [limit]
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении статистики тем: {e}')
            return []
    
    @staticmethod
    def get_active_users_24h() -> List[Dict[str, Any]]:
        """Получает активных пользователей за последние 24 часа"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_active_users_24h')
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении активных пользователей: {e}')
            return []
    
    @staticmethod
    def get_section_statistics() -> List[Dict[str, Any]]:
        """Получает статистику по разделам"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_section_statistics ORDER BY topics_count DESC')
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении статистики разделов: {e}')
            return []
    
    @staticmethod
    def get_top_contributors(limit: int = 50) -> List[Dict[str, Any]]:
        """Получает топ авторов"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_top_contributors LIMIT %s', [limit])
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении топ авторов: {e}')
            return []
    
    @staticmethod
    def get_daily_activity(days: int = 30) -> List[Dict[str, Any]]:
        """Получает активность по дням"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM v_daily_activity ORDER BY activity_date DESC LIMIT %s',
                    [days]
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении дневной активности: {e}')
            return []
    
    @staticmethod
    def get_popular_tags(limit: int = 20) -> List[Dict[str, Any]]:
        """Получает популярные теги"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_popular_tags LIMIT %s', [limit])
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении популярных тегов: {e}')
            return []
    
    @staticmethod
    def get_moderation_statistics() -> List[Dict[str, Any]]:
        """Получает статистику модерации"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_moderation_statistics')
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении статистики модерации: {e}')
            return []
    
    @staticmethod
    def get_pending_complaints() -> List[Dict[str, Any]]:
        """Получает жалобы в ожидании"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_pending_complaints')
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении ожидающих жалоб: {e}')
            return []
    
    @staticmethod
    def get_system_activity(limit: int = 100) -> List[Dict[str, Any]]:
        """Получает системную активность"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM v_system_activity LIMIT %s', [limit])
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f'Ошибка при получении системной активности: {e}')
            return []
