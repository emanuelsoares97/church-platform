"""Compat layer para permissões legadas de eventos.

Fonte de verdade: management.permissions.
Mantemos compatibilidade com o grupo legado "Gestão Eventos" nesta fase.
"""

from management.constants import GROUP_LEADERSHIP, GROUP_RECEPTION
from management.permissions import user_in_any_group


def can_manage_events(user):
    """Compatível com regras antigas e novas para gestão de eventos."""
    if not user or not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    if user_in_any_group(user, [GROUP_LEADERSHIP, GROUP_RECEPTION]):
        return True

    # Grupo legado ainda suportado por compatibilidade nesta fase.
    return user.groups.filter(name="Gestão Eventos").exists()