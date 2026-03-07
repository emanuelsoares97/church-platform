from django.contrib.auth.models import Group, User
from django.test import TestCase

from events.permissions import can_manage_events


class PermissionsTest(TestCase):
    """testa permissões de gestão de eventos."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.staff_user = User.objects.create_user(username="staff", is_staff=True)
        self.group_user = User.objects.create_user(username="groupuser")
        group = Group.objects.create(name="Gestão Eventos")
        self.group_user.groups.add(group)

    def test_can_manage_events_staff(self):
        """staff pode gerenciar eventos."""
        self.assertTrue(can_manage_events(self.staff_user))

    def test_can_manage_events_group(self):
        """utilizador no grupo pode gerenciar eventos."""
        self.assertTrue(can_manage_events(self.group_user))

    def test_can_manage_events_normal(self):
        """utilizador normal não pode gerenciar."""
        self.assertFalse(can_manage_events(self.user))

    def test_can_manage_events_anonymous(self):
        """utilizador anónimo não pode gerenciar."""
        self.assertFalse(can_manage_events(None))