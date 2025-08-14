from typing import Callable, Dict, List, Optional

from .classes.command import Command
from .classes.menu import Menu

COMMAND_REGISTRY: Dict[str, dict] = {}


def command(name: str, description: str = "", asks: Optional[List[str]] = None, kwargs_types: Optional[Dict[str, Callable]] = None, menu: Optional[str] = None):
    def decorator(func: Callable):
        command_enum = Command.from_value(name)
        arg_names = list(func.__code__.co_varnames[1:func.__code__.co_argcount])  # Fixed: co_argcount
        COMMAND_REGISTRY[name] = {
            "action": func,
            "enum": command_enum,
            "arg_names": arg_names,
            "asks": asks or [],
            "kwargs_types": kwargs_types or {},
            "menu": Menu.from_value(menu) if menu else None
        }
        print(f"Registered command: {name}, Details: {COMMAND_REGISTRY[name]}")  # Debug print
        return func

    return decorator