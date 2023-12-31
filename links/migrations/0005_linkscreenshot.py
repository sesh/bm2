# Generated by Django 4.2.3 on 2023-08-01 02:51

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("links", "0004_usersettings_hn_username"),
    ]

    operations = [
        migrations.CreateModel(
            name="LinkScreenshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("url", models.URLField(max_length=2000)),
                ("added", models.DateTimeField(auto_now_add=True)),
                ("link", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="links.link")),
            ],
        ),
    ]
