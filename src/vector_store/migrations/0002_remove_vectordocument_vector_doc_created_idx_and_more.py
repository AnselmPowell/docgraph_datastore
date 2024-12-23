# Generated by Django 5.1.1 on 2024-11-05 20:22

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vector_store', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='vectordocument',
            name='vector_doc_created_idx',
        ),
        migrations.AlterField(
            model_name='vectordocument',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='vectordocument',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
    ]
