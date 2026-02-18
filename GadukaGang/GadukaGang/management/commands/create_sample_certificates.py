from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from GadukaGang.models import Certificate, UserCertificate
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample certificates for testing'

    def handle(self, *args, **options):
        # Create sample certificates
        certificates_data = [
            {
                'name': 'Сертификат о завершении курса Python',
                'description': 'Подтверждает успешное завершение курса по основам программирования на Python',
                'criteria': {'course_id': 1}
            },
            {
                'name': 'Сертификат о завершении курса Django',
                'description': 'Подтверждает успешное завершение курса по веб-разработке с использованием Django',
                'criteria': {'course_id': 2}
            },
            {
                'name': 'Сертификат о завершении курса Flask',
                'description': 'Подтверждает успешное завершение курса по веб-разработке с использованием Flask',
                'criteria': {'course_id': 3}
            }
        ]
        
        # Create certificates
        certificates = []
        for cert_data in certificates_data:
            cert, created = Certificate.objects.get_or_create(
                name=cert_data['name'],
                defaults={
                    'description': cert_data['description'],
                    'criteria': cert_data['criteria']
                }
            )
            certificates.append(cert)
            if created:
                self.stdout.write(f'Created certificate: {cert.name}')
            else:
                self.stdout.write(f'Certificate already exists: {cert.name}')
        
        # Get all users
        users = User.objects.all()
        if not users.exists():
            self.stdout.write('No users found. Please create some users first.')
            return
        
        # Assign certificates to users
        for user in users:
            # Assign 1-3 certificates to each user
            num_certificates = random.randint(1, 3)
            user_certificates = random.sample(certificates, min(num_certificates, len(certificates)))
            
            for cert in user_certificates:
                UserCertificate.objects.get_or_create(
                    user=user,
                    certificate=cert,
                    defaults={
                        'awarded_date': timezone.now(),
                        'awarded_by': None
                    }
                )
            
            self.stdout.write(f'Assigned {len(user_certificates)} certificates to user {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample certificates and assigned them to users')
        )