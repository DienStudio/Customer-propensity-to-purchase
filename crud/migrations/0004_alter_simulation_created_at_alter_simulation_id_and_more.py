# Generated by Django 5.0.6 on 2024-05-23 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crud', '0003_delete_member'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simulation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='simulation',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='simulation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
