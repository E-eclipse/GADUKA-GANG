"""
Django management command to run security tests
"""
from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings


class Command(BaseCommand):
    help = 'Run security tests (SQL injection, encryption, etc.)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed test output',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('\n🔒 ЗАПУСК ТЕСТОВ БЕЗОПАСНОСТИ'))
        self.stdout.write('=' * 60)
        
        # Run manual security demonstration
        from GadukaGang.security_tests import run_security_tests
        
        passed, failed = run_security_tests()
        
        # Run Django tests
        self.stdout.write('\n📋 Запуск Django тестов безопасности...')
        self.stdout.write('-' * 60)
        
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=2 if verbose else 1, interactive=False)
        
        # Run only security tests
        failures = test_runner.run_tests(['GadukaGang.security_tests'])
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        if failures == 0 and failed == 0:
            self.stdout.write(self.style.SUCCESS('✅ ВСЕ ТЕСТЫ БЕЗОПАСНОСТИ ПРОЙДЕНЫ!'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Обнаружены проблемы: {failures + failed} тестов не прошли'))
        
        self.stdout.write('')
