"""
Helpers e decorators para controlo de acesso por grupos.

A ideia é centralizar nesta app toda a lógica de acesso
da área interna de gestão, para que outras apps possam
reutilizar esta base sem depender da app events.
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .constants import (
    GROUP_LEADERSHIP,
    GROUP_RECEPTION,
    GROUP_MEDIA,
    MANAGEMENT_GROUPS,
)


def user_in_group(user, group_name):
    """
    Verifica se o utilizador autenticado pertence
    ao grupo indicado.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=group_name).exists()


def user_in_any_group(user, group_names):
    """
    Verifica se o utilizador autenticado pertence
    a pelo menos um dos grupos indicados.
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True

    return user.groups.filter(name__in=group_names).exists()


def is_leadership(user):
    """
    Indica se o utilizador pertence ao grupo de liderança.
    """
    return user_in_group(user, GROUP_LEADERSHIP)


def is_reception(user):
    """
    Indica se o utilizador pertence ao grupo de receção.
    """
    return user_in_group(user, GROUP_RECEPTION)


def is_media(user):
    """
    Indica se o utilizador pertence ao grupo de mídia.
    """
    return user_in_group(user, GROUP_MEDIA)


def can_access_management(user):
    """
    Define se o utilizador pode entrar na área interna
    de gestão.
    """
    return user_in_any_group(user, MANAGEMENT_GROUPS)


def can_view_reports(user):
    """
    Apenas liderança pode ver relatórios.
    """
    return is_leadership(user)


def can_manage_registrations(user):
    """
    Liderança e receção podem gerir inscrições.
    """
    return user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_RECEPTION])


def can_manage_checkin(user):
    """
    Liderança e receção podem gerir check-in.
    """
    return user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_RECEPTION])


def can_manage_payments(user):
    """
    Liderança e receção podem gerir pagamentos.
    """
    return user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_RECEPTION])


def can_manage_gallery(user):
    """
    Exemplo de regra preparada para a galeria.

    Ajusta esta lógica conforme a tua necessidade real.
    Neste momento, liderança e mídia podem gerir esta área.
    """
    return user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_MEDIA])


def group_required(*group_names):
    """
    Decorator genérico para restringir o acesso a utilizadores
    autenticados que pertençam a pelo menos um dos grupos indicados.

    - se o utilizador não estiver autenticado, é redirecionado para login
    - se estiver autenticado mas sem permissão, recebe erro 403
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if not user_in_any_group(request.user, group_names):
                raise PermissionDenied("Não tens permissão para aceder a esta página.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def management_required(view_func):
    """
    Permite acesso a qualquer utilizador com acesso
    à área de gestão.
    """
    return group_required(*MANAGEMENT_GROUPS)(view_func)


def leadership_required(view_func):
    """
    Permite acesso apenas ao grupo de liderança.
    """
    return group_required(GROUP_LEADERSHIP)(view_func)


def reception_or_leadership_required(view_func):
    """
    Permite acesso a liderança e receção.
    """
    return group_required(GROUP_LEADERSHIP, GROUP_RECEPTION)(view_func)


def media_or_leadership_required(view_func):
    """
    Permite acesso a liderança e mídia.
    """
    return group_required(GROUP_LEADERSHIP, GROUP_MEDIA)(view_func)

def can_manage_gallery(user):
    """
    Define se o utilizador pode gerir a galeria.
    """
    return user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_MEDIA])