# Generated by Django 5.1.1 on 2025-01-04 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_assistant', '0002_searchquery_searchresult_documentrelationship_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentsection',
            name='extracted_image_text',
            field=models.TextField(null=True),
        ),
    ]
