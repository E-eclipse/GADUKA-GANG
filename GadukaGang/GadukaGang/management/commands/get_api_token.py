"""
Django management команда для создания API токена для пользователя
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт или получает API токен для пользователя'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Имя пользователя для создания токена'
        )
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Создать пользователя, если он не существует'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if not username:
            # Пытаемся найти первого суперпользователя
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # Если нет суперпользователя, берём первого пользователя
                user = User.objects.first()
            
            if not user:
                self.stdout.write(
                    self.style.ERROR('Нет пользователей в системе. Создайте пользователя сначала.')
                )
                return
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                if options.get('create_user'):
                    # Создаём нового пользователя
                    user = User.objects.create_user(
                        username=username,
                        password='password123',  # Временный пароль
                        is_staff=True,
                        is_superuser=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Создан новый пользователь: {username}')
                    )
                    self.stdout.write(
                        self.style.WARNING(f'  Пароль: password123 (измените его!)')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Пользователь {username} не найден. Используйте --create-user для создания.')
                    )
                    return
        
        # Получаем или создаём токен
        token, created = Token.objects.get_or_create(user=user)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Создан новый токен для пользователя: {user.username}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Токен для пользователя: {user.username}')
            )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'API Token: {token.key}'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write('\n📋 Как использовать:')
        self.stdout.write('\n1. Swagger UI (http://127.0.0.1:8000/api/v1/docs/):')
        self.stdout.write('   - Нажмите кнопку "Authorize" вверху справа')
        self.stdout.write(f'   - Введите: Token {token.key}')
        self.stdout.write('   - Нажмите "Authorize"')
        
        self.stdout.write('\n2. cURL:')
        self.stdout.write(f'   curl -H "Authorization: Token {token.key}" http://127.0.0.1:8000/api/v1/users/')
        
        self.stdout.write('\n3. Python requests:')
        self.stdout.write('   headers = {"Authorization": f"Token ' + token.key + '"}')
        self.stdout.write('   response = requests.get(url, headers=headers)')
        
        self.stdout.write('\n')
