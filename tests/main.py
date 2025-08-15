import os
import time

from dotenv import load_dotenv

from tests.my import HelloHandler, ByeHandler
from venantvr.telegram.bot import TelegramBot

# Assuming these are correctly defined in your project

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("ERREUR : Impossible de trouver BOT_TOKEN ou CHAT_ID.")
        print("Veuillez créer un fichier .env et y mettre vos identifiants.")
    else:
        bot = TelegramBot(bot_token=BOT_TOKEN, chat_id=CHAT_ID, handlers=[HelloHandler(), ByeHandler()])
        # my_handler = HelloHandler()
        # bot.handler = my_handler
        print(f"Bot démarré pour le chat ID {CHAT_ID}. Handlers: {bot.handlers}")
        print("Envoyez /menu, /bonjour1 ou /bonjour à votre bot.")
        print("Appuyez sur Ctrl+C pour arrêter.")

        # Send a test message to verify API connectivity
        bot.send_message({"chat_id": CHAT_ID, "text": "Bot démarré !"})

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            bot.stop()
            print("\nBot arrêté proprement.")
