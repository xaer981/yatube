# Generated by Django 2.2.16 on 2023-01-08 12:27

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20230108_1327'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-created'], 'verbose_name': 'пост', 'verbose_name_plural': 'посты'},
        ),
        migrations.RemoveField(
            model_name='post',
            name='pub_date',
        ),
        migrations.AddField(
            model_name='post',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата создания'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
    ]
