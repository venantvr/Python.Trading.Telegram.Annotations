"""Module principal pour le bot Telegram avec gestion des commandes et menus."""

import logging
import queue
import threading
import time
from typing import Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from venantvr.telegram.classes.command import Command
from venantvr.telegram.classes.enums import DynamicEnumMember
from venantvr.telegram.classes.menu import Menu
from venantvr.telegram.decorators import COMMAND_REGISTRY
from venantvr.telegram.protocols import HandlerProtocol

logger = logging.getLogger(__name__)


class TelegramBot:
    """Bot Telegram avec gestion asynchrone des messages et commandes."""

    def __init__(self, bot_token: str, chat_id: str, handlers: Optional[Union[List[HandlerProtocol], HandlerProtocol]] = None) -> None:
        """Initialise le bot Telegram.

        Args:
            bot_token: Token d'authentification du bot
            chat_id: ID du chat par défaut
            handlers: Handler(s) pour traiter les commandes
        """
        self.api_url: str = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id: str = chat_id
        self.last_update_id: Optional[int] = None
        self.incoming_queue: queue.Queue = queue.Queue()
        self.outgoing_queue: queue.Queue = queue.Queue()
        self.active_prompts: Dict[str, Dict] = {}
        self._session = self._create_session()

        # Accept single handler or list
        self.handlers: List[HandlerProtocol] = []
        if handlers is not None:
            if isinstance(handlers, (list, tuple)):
                self.handlers = list(handlers)
            else:
                self.handlers = [handlers]

        self._threads = [
            threading.Thread(target=self._receiver, daemon=True, name="receiver"),
            threading.Thread(target=self._sender, daemon=True, name="sender"),
            threading.Thread(target=self._processor, daemon=True, name="processor")
        ]
        for thread in self._threads:
            thread.start()
        logger.info(f"Bot initialisé. Token: {bot_token[:10]}..., Chat ID: {chat_id}")

    @staticmethod
    def _create_session() -> requests.Session:
        """Crée une session HTTP avec retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @staticmethod
    def _build_menu_keyboard(menu_str: str) -> Dict[str, Union[str, Dict]]:  # noqa: PLR6301
        """Construit un clavier de menu interactif.

        Args:
            menu_str: Identifiant du menu à construire

        Returns:
            Dict contenant le texte et le markup du clavier
        """
        try:
            menu_enum = Menu.from_value(menu_str)
        except ValueError as e:
            logger.error(f"Menu error: {e}")
            return {"text": f"Erreur: Menu '{menu_str}' non valide."}
        buttons = []
        for cmd_details in COMMAND_REGISTRY.values():
            if cmd_details.get('menu') == menu_enum:
                button_text = cmd_details['enum'].name.capitalize()
                buttons.append([{"text": button_text, "callback_data": cmd_details['enum'].value}])
        logger.debug(f"Menu {menu_str} buttons: {buttons}")
        return {
            "text": "Veuillez choisir une option :" if buttons else "Aucune option disponible pour ce menu.",
            "reply_markup": {"inline_keyboard": buttons}
        }

    def _receiver(self) -> None:
        """Thread de réception des messages depuis l'API Telegram."""
        while True:
            try:
                params = {"timeout": 30}
                if self.last_update_id:
                    params["offset"] = self.last_update_id + 1
                response = self._session.get(f"{self.api_url}/getUpdates", params=params, timeout=35)
                response.raise_for_status()
                updates = response.json().get("result", [])
                for update in updates:
                    self.last_update_id = update["update_id"]
                    self.incoming_queue.put(update)
                    logger.debug(f"Received update: {update}")
            except requests.RequestException as e:
                logger.error(f"Request error in _receiver: {e}")
                time.sleep(3)
            except Exception as e:
                logger.error(f"Unexpected error in _receiver: {e}")
                time.sleep(3)

    def _sender(self) -> None:
        """Thread d'envoi des messages vers l'API Telegram."""
        while True:
            payload = self.outgoing_queue.get()
            if payload is None:
                break
            try:
                response = self._session.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
                logger.debug(f"Sent message: {payload}, Response: {response.json()}")
            except Exception as e:
                logger.error(f"Error in _sender: {e}")
            self.outgoing_queue.task_done()

    def _find_handler_for_command(self, command_enum: Union[Command, DynamicEnumMember, None]) -> Optional[HandlerProtocol]:
        """Retourne le handler qui a la méthode correspondant à la commande."""
        if command_enum is None:
            return None
        cmd_details = COMMAND_REGISTRY.get(command_enum.value)
        if not cmd_details:
            return None
        method_name = cmd_details["action"].__name__
        for handler in self.handlers:
            if hasattr(handler, method_name):
                return handler
        return None

    def _processor(self) -> None:
        """Thread de traitement des messages et commandes."""
        while True:
            update = self.incoming_queue.get()
            if update is None:
                break
            logger.debug(f"Processing update: {update}")
            # noinspection PyUnusedLocal
            response_payload = None
            chat_id = None
            try:
                # Handle messages texte
                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"]
                    chat_id = str(update["message"]["chat"]["id"])
                    logger.debug(f"Received text: {text}, chat_id: {chat_id}")

                    # Menu
                    if text == "/menu":
                        response_payload = self._build_menu_keyboard("/menu")
                    elif chat_id in self.active_prompts:
                        # Traitement des prompts en cours
                        prompt_info = self.active_prompts[chat_id]
                        command_name = prompt_info['command']
                        command_details = COMMAND_REGISTRY.get(command_name)
                        if not command_details:
                            response_payload = {"text": f"Erreur: Commande '{command_name}' non trouvée."}
                        else:
                            prompt_info['arguments'].append(text)
                            num_questions = len(command_details.get("asks", []))
                            logger.debug(f"Prompt for {command_name}, args collected: {prompt_info['arguments']}, expected: {num_questions}")
                            if len(prompt_info['arguments']) < num_questions:
                                next_question_index = len(prompt_info['arguments'])
                                response_payload = {"text": command_details["asks"][next_question_index]}
                            else:
                                cmd_enum = Command.from_value(command_name)
                                handler = self._find_handler_for_command(cmd_enum)
                                if handler and cmd_enum:
                                    response_payload = handler.process_command(cmd_enum, prompt_info['arguments'])
                                    del self.active_prompts[chat_id]
                                elif not cmd_enum:
                                    logger.error(f"Command enum not found for: {command_name}")
                                    response_payload = {"text": f"Erreur: Commande '{command_name}' non valide."}
                                else:
                                    response_payload = {"text": "Erreur: Aucun handler trouvé pour cette commande."}
                                    del self.active_prompts[chat_id]
                    else:
                        command_name = text.split(' ')[0]
                        command_details = COMMAND_REGISTRY.get(command_name)
                        if command_details:
                            if command_details.get("asks"):
                                self.active_prompts[chat_id] = {'command': command_name, 'arguments': []}
                                response_payload = {"text": command_details["asks"][0]}
                            else:
                                cmd_enum = Command.from_value(command_name)
                                handler = self._find_handler_for_command(cmd_enum)
                                if handler and cmd_enum:
                                    response_payload = handler.process_command(cmd_enum, text.split(' ')[1:])
                                elif not cmd_enum:
                                    logger.error(f"Command enum not found for: {command_name}")
                                    response_payload = {"text": f"Erreur: Commande '{command_name}' non valide."}
                                else:
                                    response_payload = {"text": "Erreur: Aucun handler trouvé pour cette commande."}
                        else:
                            response_payload = {"text": f"Commande '{command_name}' non reconnue."}

                # Callback query (inline keyboard)
                elif "callback_query" in update:
                    callback_query = update["callback_query"]
                    chat_id = str(callback_query["message"]["chat"]["id"])
                    callback_data = callback_query.get("data")
                    logger.debug(f"Received callback query: {callback_data}, chat_id: {chat_id}")
                    if callback_data in COMMAND_REGISTRY:
                        command_details = COMMAND_REGISTRY.get(callback_data)
                        if command_details.get("asks"):
                            self.active_prompts[chat_id] = {'command': callback_data, 'arguments': []}
                            response_payload = {"text": command_details["asks"][0]}
                        else:
                            cmd_enum = Command.from_value(callback_data)
                            handler = self._find_handler_for_command(cmd_enum)
                            if handler and cmd_enum:
                                response_payload = handler.process_command(cmd_enum, [])
                            elif not cmd_enum:
                                logger.error(f"Callback command enum not found for: {callback_data}")
                                response_payload = {"text": f"Erreur: Commande '{callback_data}' non valide."}
                            else:
                                response_payload = {"text": "Erreur: Aucun handler trouvé pour cette commande."}
                    else:
                        response_payload = {"text": f"Action '{callback_data}' non reconnue."}

                else:
                    logger.debug(f"Non-text update received: {update}")
                    response_payload = {"text": "Désolé, je ne prends en charge que les messages texte et les actions de menu pour le moment."}

            except Exception as e:
                logger.error(f"Error in _processor: {e}", exc_info=True)
                response_payload = {"text": f"Erreur lors du traitement: {str(e)}"}

            if response_payload:
                if 'chat_id' not in response_payload:
                    response_payload['chat_id'] = chat_id or self.chat_id
                if 'text' not in response_payload:
                    response_payload['text'] = ''
                logger.debug(f"Sending response: {response_payload}")
                self.send_message(response_payload)
            self.incoming_queue.task_done()

    def send_message(self, payload: Union[Dict, List[Dict]]) -> None:
        """Envoie un ou plusieurs messages.

        Args:
            payload: Message ou liste de messages à envoyer
        """
        if isinstance(payload, dict):
            self.outgoing_queue.put(payload)
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    self.outgoing_queue.put(item)
                else:
                    logger.warning(f"Ignored non-dict item in list: {item}")
        else:
            logger.warning(f"Ignored invalid payload type: {type(payload)}")

    def stop(self) -> None:
        """Arrête proprement le bot et tous ses threads."""
        self.outgoing_queue.put(None)
        self.incoming_queue.put(None)
        if hasattr(self, '_session'):
            self._session.close()
        logger.info("Signal d'arrêt envoyé aux threads.")
