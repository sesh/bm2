# Generated by Django 4.2.2 on 2023-06-29 06:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("links", "0002_usersettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="feedbin_password",
            field=models.CharField(blank=True, help_text="Your feedbin password", max_length=300),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="feedbin_username",
            field=models.CharField(
                blank=True, help_text="Your feedbin username, probably an email address", max_length=300
            ),
        ),
    ]
