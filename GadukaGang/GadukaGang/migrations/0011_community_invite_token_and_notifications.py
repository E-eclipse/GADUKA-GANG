# Generated manually for community invite tokens and notifications

import secrets
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def generate_invite_tokens(apps, schema_editor):
    """Generate invite tokens for existing private communities"""
    Community = apps.get_model('GadukaGang', 'Community')
    for community in Community.objects.filter(is_private=True):
        if not community.invite_token:
            community.invite_token = secrets.token_urlsafe(32)
            community.save()


class Migration(migrations.Migration):

    dependencies = [
        ('GadukaGang', '0010_emailnotificationsettings_community_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='invite_token',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.RunPython(generate_invite_tokens, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='community',
            name='invite_token',
            field=models.CharField(blank=True, max_length=64, unique=True, null=True),
        ),
        migrations.CreateModel(
            name='CommunityNotificationSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notify_on_new_post', models.BooleanField(default=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_subscriptions', to='GadukaGang.community')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_notification_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('community', 'user')},
            },
        ),
    ]
