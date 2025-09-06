# Python Trading Telegram Annotations

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Une bibliothèque Python moderne pour créer des bots Telegram avec un système de commandes basé sur les annotations et décorateurs.

## 🚀 Fonctionnalités

- ✅ Gestion asynchrone des messages avec threads
- ✅ Système de commandes basé sur les décorateurs
- ✅ Support des menus interactifs (inline keyboards)
- ✅ Gestion des prompts multi-étapes
- ✅ Architecture extensible avec handlers personnalisés
- ✅ Logging structuré et gestion d'erreurs robuste
- ✅ Session HTTP avec retry automatique
- ✅ Type hints complets pour une meilleure DX

## 📦 Installation

### Installation standard

```bash
pip install -e .
```

### Installation pour le développement

```bash
pip install -e ".[dev]"
pre-commit install
```

## 🛠️ Configuration

Créez un fichier `.env` à la racine du projet :

```env
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
LOG_LEVEL=INFO  # Optionnel: DEBUG, INFO, WARNING, ERROR
```

## 🎯 Utilisation

### Exemple simple

```python
from venantvr.telegram.bot import TelegramBot
from venantvr.telegram.handler import TelegramHandler
from venantvr.telegram.decorators import command


class MySimpleHandler(TelegramHandler):
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


# Lancer le bot
bot = TelegramBot(
    bot_token="YOUR_TOKEN",
    chat_id="YOUR_CHAT_ID",
    handlers=MySimpleHandler()
)
```

## 🧪 Tests

Lancer tous les tests :

```bash
make test
```

Avec couverture de code :

```bash
python -m pytest tests/ -v --cov=venantvr --cov-report=html
```

## 🔧 Développement

### Commandes utiles

```bash
make help        # Affiche toutes les commandes disponibles
make format      # Formate le code avec black et ruff
make lint        # Vérifie le style du code
make type-check  # Vérifie les types avec mypy
make test        # Lance les tests
make check-all   # Lance toutes les vérifications
```

### Structure du projet

```
.
├── venantvr/
│   └── telegram/
│       ├── bot.py           # Classe principale du bot
│       ├── handler.py       # Gestionnaire de commandes
│       ├── decorators.py    # Décorateurs pour les commandes
│       ├── config.py        # Configuration et logging
│       └── classes/         # Types et enums
│           ├── command.py
│           ├── menu.py
│           ├── types.py
│           └── enums.py
├── tests/                   # Tests unitaires
│   ├── test_bot.py
│   ├── test_handler.py
│   └── handlers/           # Exemples de handlers
├── pyproject.toml          # Configuration du projet
├── Makefile               # Commandes de développement
└── .pre-commit-config.yaml # Hooks pre-commit
```

## 📝 Conventions de code

- **Style**: Black (ligne max: 120 caractères)
- **Linting**: Ruff
- **Type checking**: Mypy avec mode strict
- **Docstrings**: Format Google
- **Tests**: Pytest avec couverture minimum de 80%

## 🤝 Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

### Avant de soumettre

```bash
make check-all  # Vérifie tout
make pre-commit # Lance pre-commit
```

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) pour l'inspiration
- L'équipe Telegram pour leur excellente API

## 📮 Contact

- **Auteur**: venantvr
- **Email**: venantvr@gmail.com
- **GitHub**: [@venantvr](https://github.com/venantvr)