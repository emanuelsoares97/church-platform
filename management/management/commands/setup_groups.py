from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from management.constants import MANAGEMENT_GROUPS


class Command(BaseCommand):
    help = "Cria os grupos base da área interna de gestão."

    def handle(self, *args, **options):
        for group_name in MANAGEMENT_GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Grupo criado com sucesso: {group_name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"O grupo já existia: {group_name}")
                )