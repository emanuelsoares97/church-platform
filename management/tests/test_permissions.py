from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser

from management.constants import GROUP_LEADERSHIP, GROUP_RECEPTION, GROUP_MEDIA
from management.permissions import (
    user_in_group,
    user_in_any_group,
    is_leadership,
    is_reception,
    is_media,
    can_access_management,
    group_required,
    leadership_required,
    reception_or_leadership_required,
    media_or_leadership_required,
)


class UserGroupHelperFunctionsTest(TestCase):
    """Testa as funções de verificação de grupos."""

    def setUp(self):
        """Cria grupos e utilizadores de teste."""
        self.leadership_group = Group.objects.create(name=GROUP_LEADERSHIP)
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)
        self.media_group = Group.objects.create(name=GROUP_MEDIA)

        self.leadership_user = User.objects.create_user(
            username="lider", password="pass123"
        )
        self.leadership_user.groups.add(self.leadership_group)

        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.media_user = User.objects.create_user(username="media", password="pass123")
        self.media_user.groups.add(self.media_group)

        self.no_group_user = User.objects.create_user(
            username="sem_grupo", password="pass123"
        )

        self.superuser = User.objects.create_superuser(
            username="admin", password="pass123", email="admin@test.com"
        )

        self.anon_user = AnonymousUser()

    def test_user_in_group_anon_user_falso(self):
        """Utilizador anónimo não pertence a nenhum grupo."""
        self.assertFalse(user_in_group(self.anon_user, GROUP_LEADERSHIP))

    def test_user_in_group_superuser_verdadeiro(self):
        """Superuser pertence a qualquer grupo."""
        self.assertTrue(user_in_group(self.superuser, GROUP_LEADERSHIP))
        self.assertTrue(user_in_group(self.superuser, GROUP_RECEPTION))
        self.assertTrue(user_in_group(self.superuser, GROUP_MEDIA))

    def test_user_in_group_user_com_grupo_verdadeiro(self):
        """Utilizador com grupo pertence a esse grupo."""
        self.assertTrue(user_in_group(self.leadership_user, GROUP_LEADERSHIP))
        self.assertTrue(user_in_group(self.reception_user, GROUP_RECEPTION))
        self.assertTrue(user_in_group(self.media_user, GROUP_MEDIA))

    def test_user_in_group_user_sem_grupo_falso(self):
        """Utilizador sem grupo não pertence a nenhum."""
        self.assertFalse(user_in_group(self.no_group_user, GROUP_LEADERSHIP))
        self.assertFalse(user_in_group(self.no_group_user, GROUP_RECEPTION))

    def test_user_in_group_user_grupo_errado_falso(self):
        """Utilizador com grupo A não pertence ao grupo B."""
        self.assertFalse(user_in_group(self.leadership_user, GROUP_RECEPTION))
        self.assertFalse(user_in_group(self.reception_user, GROUP_MEDIA))

    def test_user_in_any_group_anon_falso(self):
        """Utilizador anónimo não pertence a nenhum grupo."""
        self.assertFalse(user_in_any_group(self.anon_user, [GROUP_LEADERSHIP]))

    def test_user_in_any_group_superuser_verdadeiro(self):
        """Superuser pertence a qualquer grupo."""
        self.assertTrue(
            user_in_any_group(self.superuser, [GROUP_LEADERSHIP, GROUP_RECEPTION])
        )

    def test_user_in_any_group_multiple_grupos_um_match(self):
        """Utilizador com um dos grupos no array satisfaz a condição."""
        self.assertTrue(
            user_in_any_group(self.leadership_user, [GROUP_LEADERSHIP, GROUP_RECEPTION])
        )
        self.assertTrue(
            user_in_any_group(
                self.reception_user, [GROUP_MEDIA, GROUP_RECEPTION, GROUP_LEADERSHIP]
            )
        )

    def test_user_in_any_group_nenhum_match(self):
        """Utilizador sem grupo correto não satisfaz."""
        self.assertFalse(user_in_any_group(self.no_group_user, [GROUP_LEADERSHIP]))
        self.assertFalse(
            user_in_any_group(self.media_user, [GROUP_LEADERSHIP, GROUP_RECEPTION])
        )

    def test_is_leadership_verdadeiro(self):
        """Verificação simplificada para liderança."""
        self.assertTrue(is_leadership(self.leadership_user))
        self.assertFalse(is_leadership(self.reception_user))
        self.assertFalse(is_leadership(self.no_group_user))
        self.assertTrue(is_leadership(self.superuser))

    def test_is_reception_verdadeiro(self):
        """Verificação simplificada para receção."""
        self.assertTrue(is_reception(self.reception_user))
        self.assertFalse(is_reception(self.leadership_user))
        self.assertFalse(is_reception(self.no_group_user))
        self.assertTrue(is_reception(self.superuser))

    def test_is_media_verdadeiro(self):
        """Verificação simplificada para mídia."""
        self.assertTrue(is_media(self.media_user))
        self.assertFalse(is_media(self.leadership_user))
        self.assertFalse(is_media(self.no_group_user))
        self.assertTrue(is_media(self.superuser))

    def test_can_access_management_leadership_verdadeiro(self):
        """Liderança pode aceder à gestão."""
        self.assertTrue(can_access_management(self.leadership_user))

    def test_can_access_management_reception_verdadeiro(self):
        """Receção pode aceder à gestão."""
        self.assertTrue(can_access_management(self.reception_user))

    def test_can_access_management_media_verdadeiro(self):
        """Mídia pode aceder à gestão."""
        self.assertTrue(can_access_management(self.media_user))

    def test_can_access_management_no_group_falso(self):
        """Utilizador sem grupo não pode aceder."""
        self.assertFalse(can_access_management(self.no_group_user))


class DecoratorGroupRequiredTest(TestCase):
    """Testa o decorator group_required e variações."""

    def setUp(self):
        """Cria grupos, utilizadores e factory para requests."""
        self.leadership_group = Group.objects.create(name=GROUP_LEADERSHIP)
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)

        self.leadership_user = User.objects.create_user(
            username="lider", password="pass123"
        )
        self.leadership_user.groups.add(self.leadership_group)

        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.no_group_user = User.objects.create_user(
            username="sem_grupo", password="pass123"
        )

        self.factory = RequestFactory()

    def create_view_with_decorator(self, *groups):
        """Factory que cria uma view protegida com o decorator."""
        @group_required(*groups)
        def protected_view(request):
            return "OK"

        return protected_view

    def test_group_required_anon_redireciona_para_login(self):
        """Utilizador anónimo é redirecionado para login."""
        view = self.create_view_with_decorator(GROUP_LEADERSHIP)
        request = self.factory.get("/test/")
        request.user = AnonymousUser()

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_group_required_user_com_grupo_acede(self):
        """Utilizador com grupo correto acede."""
        from django.http import HttpResponse

        view = self.create_view_with_decorator(GROUP_LEADERSHIP)

        request = self.factory.get("/test/")
        request.user = self.leadership_user

        # Mockamos a resposta
        result = view(request)
        self.assertEqual(result, "OK")

    def test_group_required_user_sem_grupo_403(self):
        """Utilizador sem grupo correto levanta PermissionDenied."""
        view = self.create_view_with_decorator(GROUP_LEADERSHIP)
        request = self.factory.get("/test/")
        request.user = self.no_group_user

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            view(request)

    def test_group_required_user_outro_grupo_403(self):
        """Utilizador com outro grupo levanta PermissionDenied."""
        view = self.create_view_with_decorator(GROUP_LEADERSHIP)
        request = self.factory.get("/test/")
        request.user = self.reception_user

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            view(request)

    def test_group_required_multiple_grupos_um_ok(self):
        """Utilizador com um dos múltiplos grupos acede."""
        view = self.create_view_with_decorator(GROUP_LEADERSHIP, GROUP_RECEPTION)
        request = self.factory.get("/test/")
        request.user = self.reception_user

        result = view(request)
        self.assertEqual(result, "OK")

    def test_leadership_required_decorator(self):
        """Decorator leadership_required funciona corretamente."""

        @leadership_required
        def protected_view(request):
            return "OK"

        request = self.factory.get("/test/")
        request.user = self.leadership_user
        result = protected_view(request)
        self.assertEqual(result, "OK")

        request.user = self.reception_user
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            protected_view(request)

    def test_reception_or_leadership_required_decorator(self):
        """Decorator reception_or_leadership_required funciona corretamente."""

        @reception_or_leadership_required
        def protected_view(request):
            return "OK"

        request = self.factory.get("/test/")

        request.user = self.leadership_user
        result = protected_view(request)
        self.assertEqual(result, "OK")

        request.user = self.reception_user
        result = protected_view(request)
        self.assertEqual(result, "OK")

        request.user = self.no_group_user
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            protected_view(request)

    def test_media_or_leadership_required_decorator(self):
        """Decorator media_or_leadership_required funciona corretamente."""
        media_group = Group.objects.create(name=GROUP_MEDIA)
        media_user = User.objects.create_user(username="media", password="pass123")
        media_user.groups.add(media_group)

        @media_or_leadership_required
        def protected_view(request):
            return "OK"

        request = self.factory.get("/test/")

        request.user = self.leadership_user
        result = protected_view(request)
        self.assertEqual(result, "OK")

        request.user = media_user
        result = protected_view(request)
        self.assertEqual(result, "OK")

        request.user = self.reception_user
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            protected_view(request)
