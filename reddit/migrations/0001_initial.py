# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('ups', models.IntegerField(default=0)),
                ('downs', models.IntegerField(default=0)),
                ('score', models.IntegerField(default=0)),
                ('raw_comment', models.TextField(blank=True)),
                ('html_comment', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RedditUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=250)),
                ('url', models.URLField(null=True, blank=True)),
                ('text', models.TextField(max_length=5000, blank=True)),
                ('ups', models.IntegerField(default=0)),
                ('downs', models.IntegerField(default=0)),
                ('score', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('comment_count', models.IntegerField(default=0)),
                ('author', models.ForeignKey(to='reddit.RedditUser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vote_object_id', models.PositiveIntegerField()),
                ('value', models.IntegerField(default=0)),
                ('submission', models.ForeignKey(to='reddit.Submission')),
                ('user', models.ForeignKey(to='reddit.RedditUser')),
                ('vote_object_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(to='reddit.RedditUser'),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(related_name='children', to='reddit.Comment', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(to='reddit.Submission'),
        ),
    ]
