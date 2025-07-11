# Generated by Django 5.2.1 on 2025-07-01 00:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_grouptask'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonalEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='予定名')),
                ('description', models.TextField(blank=True, verbose_name='詳細')),
                ('start_time', models.DateTimeField(verbose_name='開始日時')),
                ('end_time', models.DateTimeField(blank=True, help_text='終日の予定の場合は空欄にしてください', null=True, verbose_name='終了日時')),
                ('is_all_day', models.BooleanField(default=False, verbose_name='終日')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '個人予定',
                'verbose_name_plural': '個人予定',
                'ordering': ['start_time'],
            },
        ),
    ]
