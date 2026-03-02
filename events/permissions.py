def can_manage_events(user):
    if not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name="Gestão Eventos").exists()