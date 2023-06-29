# Example management command
# https://docs.djangoproject.com/en/4.0/howto/custom-management-commands/

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "An example management command created by djbs"

    def handle(self, *args, **options):
        self.stdout.write("Configure your management commands here...")
        raise CommandError("Management command not implemented")
