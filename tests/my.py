from venantvr.telegram.decorators import command, COMMAND_REGISTRY
from venantvr.telegram.handler import TelegramHandler


class ByeHandler(TelegramHandler):
    @command(name="/menu", description="Afficher le menu d'aide", menu="/menu")
    def menu(self) -> dict:
        text_response = "Voici les commandes disponibles à taper :\n"
        for cmd_name, cmd_details in COMMAND_REGISTRY.items():
            description = cmd_details.get("description", "Pas de description.")
            text_response += f"\n• `{cmd_name}` : {description}"
        return {"text": text_response, "parse_mode": "Markdown"}

    @command(
        name="/bye",
        description="Salutation simple sans arguments",
        asks=[],
        kwargs_types={},
        menu="/menu"
    )
    def bye(self) -> dict:
        return {"text": "Bye !!!!!"}


class HelloHandler(TelegramHandler):
    @command(name="/menu", description="Afficher le menu d'aide", menu="/menu")
    def menu(self) -> dict:
        text_response = "Voici les commandes disponibles à taper :\n"
        for cmd_name, cmd_details in COMMAND_REGISTRY.items():
            description = cmd_details.get("description", "Pas de description.")
            text_response += f"\n• `{cmd_name}` : {description}"
        return {"text": text_response, "parse_mode": "Markdown"}

    @command(
        name="/hello",
        description="Salutation simple sans arguments",
        asks=[],
        kwargs_types={},
        menu="/menu"
    )
    def hello(self) -> dict:
        return {"text": "Bonjour !!!!!"}

    @command(
        name="/bonjour",
        description="Salutation personnalisée avec nom et âge",
        asks=[
            "Quel est votre nom ?",
            "Quel est votre âge ?"
        ],
        kwargs_types={
            "name": str,
            "age": int
        },
        menu="/menu"
    )
    def bonjour(self, name: str, age: int) -> dict:
        if age < 18:
            message_age = "vous êtes jeune !"
        else:
            message_age = "vous êtes un adulte."
        return {"text": f"Bonjour, {name} ! À {age} ans, {message_age}"}
