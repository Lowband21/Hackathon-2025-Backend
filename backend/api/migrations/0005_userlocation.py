# Generated by Django 5.2 on 2025-04-27 02:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_personalityquestion_domain_personalityquestion_facet_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False, help_text='Is the user active (did they have the app open when this ping was made)?')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['last_updated'], name='api_userloc_last_up_14560d_idx'), models.Index(fields=['is_active'], name='api_userloc_is_acti_728718_idx')],
            },
        ),
    ]
