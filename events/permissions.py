def can_manage_events(user):
    """verifica se utilizador pode gerenciar eventos (staff ou grupo específico)."""
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name="Gestão Eventos").exists()