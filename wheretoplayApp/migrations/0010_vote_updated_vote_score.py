# Generated by Django 5.1.1 on 2024-11-15 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wheretoplayApp', '0009_alter_workspace_code_alter_workspace_url_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='updated_vote_score',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
