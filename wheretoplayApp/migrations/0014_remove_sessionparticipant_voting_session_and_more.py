# Generated by Django 5.1.1 on 2024-11-25 22:48

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wheretoplayApp', '0013_workspace_outlier_threshold'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessionparticipant',
            name='voting_session',
        ),
        migrations.AddField(
            model_name='sessionparticipant',
            name='guest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.guest'),
        ),
        migrations.AddField(
            model_name='sessionparticipant',
            name='workspace',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.workspace'),
        ),
        migrations.AddField(
            model_name='vote',
            name='guest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.guest'),
        ),
        migrations.AddField(
            model_name='workspace',
            name='guest_cap',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='workspace',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.workspace'),
        ),
        migrations.AlterField(
            model_name='usercategory',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='vote',
            name='opportunity',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.opportunity'),
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('invitation_id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wheretoplayApp.guest')),
                ('workspace', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wheretoplayApp.workspace')),
            ],
            options={
                'db_table': 'invitation',
                'managed': True,
            },
        ),
        migrations.DeleteModel(
            name='VotingSession',
        ),
    ]
