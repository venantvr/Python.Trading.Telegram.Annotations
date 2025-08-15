# venantvr/telegram/decorators.py
from typing import Callable, Dict, List, Optional

from venantvr.telegram.classes.command import Command
from venantvr.telegram.classes.menu import Menu

COMMAND_REGISTRY: Dict[str, dict] = {}

def command(name: str, description: str = "", asks: Optional[List[str]] = None, kwargs_types: Optional[Dict[str, Callable]] = None, menu: Optional[str] = None):
    def decorator(func: Callable):
        command_enum = Command.from_value(name)
        arg_names = list(func.__code__.co_varnames[1:func.__code__.co_argcount])
        # Trouver le handler auquel la méthode appartient
        handler_class = None
        if hasattr(func, '__self__'):
            handler_class = func.__self__.__class__
        elif func.__qualname__.split('.')[:-1]:  # Si c'est une méthode de classe
            class_name = func.__qualname__.split('.')[-2]
            handler_class = globals().get(class_name)  # Note : ceci peut nécessiter un ajustement selon votre structure
        COMMAND_REGISTRY[name] = {
            "action": func,
            "enum": command_enum,
            "arg_names": arg_names,
            "asks": asks or [],
            "kwargs_types": kwargs_types or {},
            "menu": Menu.from_value(menu) if menu else None,
            "handler": handler_class  # Ajout Ernst: Ajouter le handler à l'entrée du registre
        }
        print(f"Registered command: {name}, Details: {COMMAND_REGISTRY[name]}")
        return func
    return decorator
