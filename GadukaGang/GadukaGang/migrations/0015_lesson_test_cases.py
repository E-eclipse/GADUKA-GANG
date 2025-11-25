# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GadukaGang', '0014_lesson_test_input_test_output'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='test_cases',
            field=models.JSONField(blank=True, default=list),
        ),
    ]

