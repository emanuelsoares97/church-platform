"""
Context processor com flags de acesso da área de gestão.

Isto evita repetir lógica nos templates e permite esconder
links e botões conforme o grupo do utilizador.
"""

from management.permissions import (
    can_access_management,
    can_manage_checkin,
    can_manage_gallery,
    can_manage_payments,
    can_manage_registrations,
    can_view_reports,
)


def management_access(request):
    """
    Disponibiliza flags globais de acesso para os templates.
    """
    user = request.user

    return {
        "can_access_management": can_access_management(user),
        "can_manage_registrations": can_manage_registrations(user),
        "can_manage_payments": can_manage_payments(user),
        "can_manage_checkin": can_manage_checkin(user),
        "can_manage_gallery": can_manage_gallery(user),
        "can_view_reports": can_view_reports(user),
    }