# Generated by Django 5.1.4 on 2025-03-16 15:21

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_assistant', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='searchresult',
            name='processing_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=50),
        ),
        migrations.AddIndex(
            model_name='searchresult',
            index=models.Index(fields=['processing_status'], name='search_resu_process_c15345_idx'),
        ),
    ]
