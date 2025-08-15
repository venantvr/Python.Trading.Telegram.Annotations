from typing import Optional

from venantvr.telegram.classes.command import Command
from venantvr.telegram.decorators import command, COMMAND_REGISTRY


class TelegramHandler:
    def process_command(self, command: Command, arguments: list) -> Optional[dict]:
        command_details = COMMAND_REGISTRY.get(command.value)
        if not command_details:
            print(f"Command not found: {command.value}")  # Debug print
            return {"text": f"Erreur: Commande '{command.value}' non trouvée."}

        action_func = command_details.get("action")
        arg_names = command_details.get("arg_names", [])
        kwargs_types = command_details.get("kwargs_types", {})

        if len(arguments) != len(arg_names):
            print(f"Argument mismatch for {command.value}: expected {len(arg_names)}, got {len(arguments)}")  # Debug print
            return {"text": f"Erreur: Nombre d'arguments incorrect. Attendu: {len(arg_names)}, Reçu: {len(arguments)}"}

        kwargs = {}
        for i, arg_name in enumerate(arg_names):
            try:
                expected_type = kwargs_types.get(arg_name, str)
                kwargs[arg_name] = expected_type(arguments[i])
            except (ValueError, TypeError) as e:
                print(f"Argument error for '{arg_name}' in {command.value}: {e}")  # Debug print
                return {"text": f"L'argument '{arguments[i]}' pour '{arg_name}' est invalide. Type attendu: {expected_type.__name__}."}

        if hasattr(self, action_func.__name__):
            bound_action = getattr(self, action_func.__name__)
            response = bound_action(**kwargs)
            print(f"Command {command.value} executed, response: {response}")  # Debug print
            return response
        print(f"Action {action_func.__name__} not found in handler")  # Debug print
        return {"text": f"Erreur: Action pour '{command.value}' non trouvée."}

    def bonjour(self):
        return {"text": f"Bonjour {self.__class__.__name__}",
                "reply_markup": ""}

    @staticmethod
    @command(
        name="/help",
        description="Liste tous les menus disponibles",
        menu=None  # Pas associé à un menu spécifique
    )
    def help(self) -> dict:
        """Commande /help qui liste dynamiquement tous les menus référencés dans COMMAND_REGISTRY."""
        text_response = "Voici les menus disponibles :\n"
        seen_menus = set()

        # Parcourir COMMAND_REGISTRY pour trouver les menus uniques
        for cmd_name, cmd_details in COMMAND_REGISTRY.items():
            menu = cmd_details.get("menu")
            if menu and menu.value != "/menu" and menu.value not in seen_menus:
                seen_menus.add(menu.value)
                # Générer une description dynamique
                description = f"Menu {menu.value.lstrip('/').capitalize()}"
                # Si la commande est un menu (par exemple, /positions avec action 'menu'), utiliser sa description
                if cmd_name == menu.value and cmd_details.get("action").__name__ == "menu":
                    description = cmd_details.get("description", description)
                text_response += f"\n• `{menu.value}` : {description}"

        if not seen_menus:
            text_response = "Aucun menu disponible pour le moment."

        return {"text": text_response, "parse_mode": "Markdown"}