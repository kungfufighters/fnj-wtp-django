# Generated by Django 5.1.1 on 2024-10-29 01:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wheretoplayApp', '0005_remove_opportunity_opp_category_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VotesFor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.workspace')),
            ],
            options={
                'db_table': 'votes_for',
                'managed': True,
            },
        ),
    ]
