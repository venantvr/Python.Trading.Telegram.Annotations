from venantvr.telegram.classes.enums import DynamicEnum


class Menu(DynamicEnum):
    """
    Enum dynamique pour les menus. Les membres sont injectés au démarrage
    via la méthode `Menu.register({...})`.
    """
    # Les membres comme NULL, BOT, etc. seront ajoutés dynamiquement.
    pass
