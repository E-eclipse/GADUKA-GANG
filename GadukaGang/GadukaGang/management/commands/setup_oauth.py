from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

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
        
        # Create GitHub OAuth app
        github_app = SocialApp.objects.create(
            provider='github',
            name='GitHub OAuth',
            client_id='Ov23lieNLQVHELWIif5Y',
            secret='c7a728d241aad3692a417c3cff487208e501af7b'
        )
        github_app.sites.add(site)
        self.stdout.write('Created GitHub OAuth app')
        
        # Create Google OAuth app
        google_app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth',
            client_id='577335155855-iggc9dtajj7b5ke0mulf4o86vs3nj99e.apps.googleusercontent.com',
            secret='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'
        )
        google_app.sites.add(site)
        self.stdout.write('Created Google OAuth app')
        
        self.stdout.write('Successfully setup OAuth applications')