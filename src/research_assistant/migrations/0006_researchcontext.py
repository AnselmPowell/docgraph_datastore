# Generated by Django 5.1.4 on 2025-03-21 09:27

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_assistant', '0005_note'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ResearchContext',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='research_context', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'research_contexts',
                'constraints': [models.UniqueConstraint(fields=('user',), name='one_context_per_user')],
            },
        ),
    ]
