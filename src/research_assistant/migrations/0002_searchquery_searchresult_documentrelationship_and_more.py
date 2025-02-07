# Generated by Django 5.1.1 on 2025-01-04 01:47

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_assistant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchQuery',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('context', models.TextField()),
                ('theme', models.CharField(max_length=200)),
                ('keywords', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('documents', models.ManyToManyField(related_name='searches', to='research_assistant.documentmetadata')),
            ],
            options={
                'db_table': 'search_queries',
            },
        ),
        migrations.CreateModel(
            name='SearchResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('relevance_score', models.FloatField()),
                ('matching_sections', models.JSONField(default=list)),
                ('context_matches', models.JSONField(default=list)),
                ('theme_matches', models.JSONField(default=list)),
                ('keyword_matches', models.JSONField(default=list)),
                ('citation_matches', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='research_assistant.documentmetadata')),
                ('search_query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='research_assistant.searchquery')),
            ],
            options={
                'db_table': 'search_results',
            },
        ),
        migrations.CreateModel(
            name='DocumentRelationship',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('relationship_type', models.CharField(max_length=100)),
                ('confidence_score', models.FloatField()),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_relationships', to='research_assistant.documentmetadata')),
                ('target_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_relationships', to='research_assistant.documentmetadata')),
            ],
            options={
                'db_table': 'document_relationships',
                'indexes': [models.Index(fields=['source_document', 'target_document'], name='document_re_source__2718f5_idx'), models.Index(fields=['relationship_type'], name='document_re_relatio_035f14_idx'), models.Index(fields=['confidence_score'], name='document_re_confide_a70bea_idx')],
            },
        ),
        migrations.CreateModel(
            name='LLMResponseCache',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('response_type', models.CharField(max_length=50)),
                ('query_hash', models.TextField()),
                ('response_data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='llm_responses', to='research_assistant.documentmetadata')),
            ],
            options={
                'db_table': 'llm_response_cache',
                'indexes': [models.Index(fields=['document', 'response_type', 'query_hash'], name='llm_respons_documen_bc5eb8_idx'), models.Index(fields=['created_at'], name='llm_respons_created_e754e9_idx')],
                'unique_together': {('document', 'response_type', 'query_hash')},
            },
        ),
        migrations.AddIndex(
            model_name='searchquery',
            index=models.Index(fields=['created_at'], name='search_quer_created_02141d_idx'),
        ),
        migrations.AddIndex(
            model_name='searchquery',
            index=models.Index(fields=['theme'], name='search_quer_theme_a0301c_idx'),
        ),
        migrations.AddIndex(
            model_name='searchresult',
            index=models.Index(fields=['search_query', 'document'], name='search_resu_search__ecb470_idx'),
        ),
        migrations.AddIndex(
            model_name='searchresult',
            index=models.Index(fields=['relevance_score'], name='search_resu_relevan_75610c_idx'),
        ),
        migrations.AddIndex(
            model_name='searchresult',
            index=models.Index(fields=['created_at'], name='search_resu_created_51526a_idx'),
        ),
    ]
