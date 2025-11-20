from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = 'Setup OAuth applications for GitHub and Google'

    def handle(self, *args, **options):
        # Get or create site
        site, created = Site.objects.get_or_create(
            domain='localhost:9876',
            defaults={'name': 'localhost:9876'}
        )
        
        if created:
            self.stdout.write(f'Created site: {site.domain}')
        else:
            self.stdout.write(f'Using existing site: {site.domain}')
            
        # Delete existing social apps
        SocialApp.objects.all().delete()
        self.stdout.write('Deleted existing social apps')
        
        # Create GitHub OAuth app (only if credentials are provided in .env)
        github_client_id = os.getenv('GITHUB_OAUTH_CLIENT_ID')
        github_secret = os.getenv('GITHUB_OAUTH_SECRET')
        
        if github_client_id and github_secret:
            github_app = SocialApp.objects.create(
                provider='github',
                name='GitHub OAuth',
                client_id=github_client_id,
                secret=github_secret
            )
            github_app.sites.add(site)
            self.stdout.write('Created GitHub OAuth app')
        else:
            self.stdout.write(self.style.WARNING('Skipped GitHub OAuth: credentials not found in .env'))
        
        # Create Google OAuth app (only if credentials are provided in .env)
        google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        google_secret = os.getenv('GOOGLE_OAUTH_SECRET')
        
        if google_client_id and google_secret:
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth',
                client_id=google_client_id,
                secret=google_secret
            )
            google_app.sites.add(site)
            self.stdout.write('Created Google OAuth app')
        else:
            self.stdout.write(self.style.WARNING('Skipped Google OAuth: credentials not found in .env'))
        
        self.stdout.write('Successfully setup OAuth applications')