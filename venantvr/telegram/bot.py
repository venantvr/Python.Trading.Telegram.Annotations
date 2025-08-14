import queue
import threading
import time

import requests

from venantvr.telegram.classes.command import Command
from venantvr.telegram.classes.menu import Menu
from venantvr.telegram.decorators import COMMAND_REGISTRY


class TelegramBot:
    def __init__(self, bot_token, chat_id):
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self.last_update_id = None
        self.incoming_queue = queue.Queue()
        self.outgoing_queue = queue.Queue()
        self.handler = None
        self.active_prompts = {}

        threading.Thread(target=self._receiver, daemon=True).start()
        threading.Thread(target=self._sender, daemon=True).start()
        threading.Thread(target=self._processor, daemon=True).start()
        print(f"Bot initialisé. Token: {bot_token[:10]}..., Chat ID: {chat_id}")

    def _build_menu_keyboard(self, menu_str: str) -> dict:
        """Construit un clavier de menu."""
        try:
            menu_enum = Menu.from_value(menu_str)
        except ValueError as e:
            print(f"Menu error: {e}")
            return {"text": f"Erreur: Menu '{menu_str}' non valide."}
        buttons = []
        for cmd_details in COMMAND_REGISTRY.values():
            if cmd_details.get('menu') == menu_enum:
                button_text = cmd_details['enum'].name.capitalize()
                buttons.append([{"text": button_text, "callback_data": cmd_details['enum'].value}])
        print(f"Menu {menu_str} buttons: {buttons}")  # Debug print
        return {
            "text": "Veuillez choisir une option :" if buttons else "Aucune option disponible pour ce menu.",
            "reply_markup": {"inline_keyboard": buttons}
        }

    def _receiver(self):
        while True:
            try:
                params = {"timeout": 30}
                if self.last_update_id:
                    params["offset"] = self.last_update_id + 1
                response = requests.get(f"{self.api_url}/getUpdates", params=params, timeout=35)
                response.raise_for_status()
                updates = response.json().get("result", [])
                for update in updates:
                    self.last_update_id = update["update_id"]
                    self.incoming_queue.put(update)
                    print(f"Received update: {update}")  # Debug print
            except requests.RequestException as e:
                print(f"Request error in _receiver: {e}")
                time.sleep(3)
            except Exception as e:
                print(f"Error in _receiver: {e}")
                time.sleep(3)

    def _sender(self):
        while True:
            payload = self.outgoing_queue.get()
            if payload is None:
                break
            try:
                response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
                print(f"Sent message: {payload}, Response: {response.json()}")  # Debug print
            except Exception as e:
                print(f"Error in _sender: {e}")
            self.outgoing_queue.task_done()

    def _processor(self):
        while True:
            update = self.incoming_queue.get()
            if update is None:
                break
            print(f"Processing update: {update}")  # Debug print
            response_payload = None
            chat_id = None
            try:
                # Handle all update types
                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"]
                    chat_id = str(update["message"]["chat"]["id"])
                    print(f"Received text: {text}, chat_id: {chat_id}")  # Debug print

                    # Handle commands and prompts
                    if text == "/menu":
                        response_payload = self._build_menu_keyboard("/menu")
                    elif chat_id in self.active_prompts:
                        prompt_info = self.active_prompts[chat_id]
                        command_name = prompt_info['command']
                        command_details = COMMAND_REGISTRY.get(command_name)
                        if not command_details:
                            response_payload = {"text": f"Erreur: Commande '{command_name}' non trouvée."}
                        else:
                            prompt_info['arguments'].append(text)
                            num_questions = len(command_details.get("asks", []))
                            print(f"Prompt for {command_name}, args collected: {prompt_info['arguments']}, expected: {num_questions}")  # Debug print
                            if len(prompt_info['arguments']) < num_questions:
                                next_question_index = len(prompt_info['arguments'])
                                response_payload = {"text": command_details["asks"][next_question_index]}
                            else:
                                try:
                                    cmd_enum = Command.from_value(command_name)
                                    if self.handler:
                                        response_payload = self.handler.process_command(cmd_enum, prompt_info['arguments'])
                                    else:
                                        response_payload = {"text": "Erreur: Handler non défini."}
                                    del self.active_prompts[chat_id]
                                except ValueError as e:
                                    print(f"Command enum error: {e}")
                                    response_payload = {"text": f"Erreur: Commande '{command_name}' non valide."}
                    else:
                        command_name = text.split(' ')[0]
                        command_details = COMMAND_REGISTRY.get(command_name)
                        if command_details:
                            if command_details.get("asks"):
                                self.active_prompts[chat_id] = {'command': command_name, 'arguments': []}
                                response_payload = {"text": command_details["asks"][0]}
                            else:
                                try:
                                    cmd_enum = Command.from_value(command_name)
                                    if self.handler:
                                        response_payload = self.handler.process_command(cmd_enum, text.split(' ')[1:])
                                    else:
                                        response_payload = {"text": "Erreur: Handler non défini."}
                                except ValueError as e:
                                    print(f"Command enum error: {e}")
                                    response_payload = {"text": f"Erreur: Commande '{command_name}' non valide."}
                        else:
                            response_payload = {"text": f"Commande '{command_name}' non reconnue."}
                # Handle callback queries (e.g., from inline keyboard buttons)
                elif "callback_query" in update:
                    callback_query = update["callback_query"]
                    chat_id = str(callback_query["message"]["chat"]["id"])
                    callback_data = callback_query.get("data")
                    print(f"Received callback query: {callback_data}, chat_id: {chat_id}")  # Debug print
                    if callback_data in COMMAND_REGISTRY:
                        command_details = COMMAND_REGISTRY.get(callback_data)
                        if command_details.get("asks"):
                            self.active_prompts[chat_id] = {'command': callback_data, 'arguments': []}
                            response_payload = {"text": command_details["asks"][0]}
                        else:
                            try:
                                cmd_enum = Command.from_value(callback_data)
                                if self.handler:
                                    response_payload = self.handler.process_command(cmd_enum, [])
                                else:
                                    response_payload = {"text": "Erreur: Handler non défini."}
                            except ValueError as e:
                                print(f"Callback command enum error: {e}")
                                response_payload = {"text": f"Erreur: Commande '{callback_data}' non valide."}
                    else:
                        response_payload = {"text": f"Action '{callback_data}' non reconnue."}
                else:
                    print(f"Non-text update received: {update}")  # Debug print
                    response_payload = {"text": "Désolé, je ne prends en charge que les messages texte et les actions de menu pour le moment."}
            except Exception as e:
                print(f"Error in _processor: {e}")
                response_payload = {"text": f"Erreur lors du traitement: {str(e)}"}

            if response_payload:
                if 'chat_id' not in response_payload:
                    response_payload['chat_id'] = chat_id or self.chat_id
                if 'text' not in response_payload:
                    response_payload['text'] = ''
                print(f"Sending response: {response_payload}")  # Debug print
                self.send_message(response_payload)
            self.incoming_queue.task_done()

    def send_message(self, payload: dict):
        self.outgoing_queue.put(payload)

    def stop(self):
        self.outgoing_queue.put(None)
        self.incoming_queue.put(None)
        print("Signal d'arrêt envoyé aux threads.")