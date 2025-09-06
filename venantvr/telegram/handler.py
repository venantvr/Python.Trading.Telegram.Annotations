"""Module de gestion des handlers pour les commandes Telegram."""

import logging
from typing import Any, Dict, List, Optional, Union

from venantvr.telegram.classes.command import Command
from venantvr.telegram.classes.enums import DynamicEnumMember
from venantvr.telegram.decorators import COMMAND_REGISTRY, command

logger = logging.getLogger(__name__)


class TelegramHandler:
    """Classe de base pour gérer les commandes Telegram."""

    def process_command(self, cmd: Union[Command, DynamicEnumMember], arguments: List[Any]) -> Optional[Dict[str, Any]]:
        """Traite une commande avec ses arguments.

        Args:
            cmd: L'enum de la commande à exécuter
            arguments: Liste des arguments de la commande

        Returns:
            Dict avec la réponse ou None en cas d'erreur
        """
        command_details = COMMAND_REGISTRY.get(cmd.value)
        if not command_details:
            logger.error(f"Command not found: {cmd.value}")
            return {"text": f"Erreur: Commande '{cmd.value}' non trouvée."}

        action_func = command_details.get("action")
        arg_names = command_details.get("arg_names", [])
        kwargs_types = command_details.get("kwargs_types", {})

        if len(arguments) != len(arg_names):
            logger.error(f"Argument mismatch for {cmd.value}: expected {len(arg_names)}, got {len(arguments)}")
            return {"text": f"Erreur: Nombre d'arguments incorrect. Attendu: {len(arg_names)}, Reçu: {len(arguments)}"}

        kwargs = {}
        for i, arg_name in enumerate(arg_names):
            expected_type = kwargs_types.get(arg_name, str)
            try:
                kwargs[arg_name] = expected_type(arguments[i])
            except (ValueError, TypeError) as e:
                logger.error(f"Argument error for '{arg_name}' in {cmd.value}: {e}")
                return {"text": f"L'argument '{arguments[i]}' pour '{arg_name}' est invalide. Type attendu: {expected_type.__name__}."}

        if hasattr(self, action_func.__name__):
            bound_action = getattr(self, action_func.__name__)
            response = bound_action(**kwargs)
            logger.debug(f"Command {cmd.value} executed, response: {response}")
            return response
        logger.error(f"Action {action_func.__name__} not found in handler")
        return {"text": f"Erreur: Action pour '{cmd.value}' non trouvée."}

    def bonjour(self) -> Dict[str, str]:
        """Commande de salutation par défaut.

        Returns:
            Dict avec le message de salutation
        """
        return {"text": f"Bonjour {self.__class__.__name__}",
                "reply_markup": ""}

    @staticmethod
    @command(
        name="/help",
        description="Liste toutes les commandes disponibles",
        menu="/menu"
    )
    def help() -> Dict[str, str]:
        """Commande /help qui liste toutes les commandes distinctes par menu.

        Returns:
            Dict avec la liste des commandes formatée en Markdown
        """
        try:
            seen_menus = set()
            text_response = "Voici toutes les commandes disponibles :\n"
            for cmd_name, cmd_details in COMMAND_REGISTRY.items():
                menu = cmd_details.get("menu")
                if menu and menu.value != "/menu" and menu not in seen_menus:
                    seen_menus.add(menu)
                    description = cmd_details.get("description", "Pas de description.")
                    text_response += f"\n• `{menu.value}` : {description}"
            return {"text": text_response, "parse_mode": "Markdown"}
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            return {"text": "Erreur lors de la génération de l'aide."}
