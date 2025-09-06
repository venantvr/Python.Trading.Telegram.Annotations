import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

from venantvr.telegram.classes.command import Command
from venantvr.telegram.classes.menu import Menu

logger = logging.getLogger(__name__)

COMMAND_REGISTRY: Dict[str, dict] = {}


def command(name: str, description: str = "", asks: Optional[List[str]] = None,
            kwargs_types: Optional[Dict[str, Callable]] = None,
            menu: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        command_enum = Command.from_value(name)

        # Obtenir les noms d'arguments de la fonction de manière plus robuste
        sig = inspect.signature(func)
        arg_names = [param.name for param in sig.parameters.values() if param.name != 'self']

        COMMAND_REGISTRY[name] = {
            "action": func,
            "enum": command_enum,
            "arg_names": arg_names,
            "asks": asks or [],
            "kwargs_types": kwargs_types or {},
            "menu": Menu.from_value(menu) if menu else None,
            "description": description  # Stocker la description
        }
        logger.debug(f"Registered command: {name}")
        return func

    return decorator
