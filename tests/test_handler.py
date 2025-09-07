"""Tests unitaires pour le module TelegramHandler."""

import unittest
from unittest.mock import Mock, patch

from venantvr.telegram.classes.command import Command
from venantvr.telegram.handler import TelegramHandler


class TestTelegramHandler(unittest.TestCase):
    """Tests pour la classe TelegramHandler."""

    def setUp(self) -> None:
        """Initialisation avant chaque test."""
        self.handler = TelegramHandler()

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    def test_process_command_not_found(self, mock_registry):
        """Test le traitement d'une commande non trouvée."""
        mock_command = Mock(spec=Command)
        mock_command.value = "/unknown"
        mock_registry.get.return_value = None

        result = self.handler.process_command(mock_command, [])

        self.assertIn("Erreur", result["text"])
        self.assertIn("non trouvée", result["text"])

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    def test_process_command_wrong_arguments(self, mock_registry):
        """Test avec un nombre incorrect d'arguments."""
        mock_command = Mock(spec=Command)
        mock_command.value = "/test"
        mock_registry.get.return_value = {"action": Mock(), "arg_names": ["arg1", "arg2"], "kwargs_types": {}}

        result = self.handler.process_command(mock_command, ["only_one"])

        self.assertIn("Erreur", result["text"])
        self.assertIn("incorrect", result["text"])

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    def test_process_command_type_conversion_error(self, mock_registry):
        """Test avec une erreur de conversion de type."""
        mock_command = Mock(spec=Command)
        mock_command.value = "/test"
        mock_registry.get.return_value = {
            "action": Mock(__name__="test_action"),
            "arg_names": ["number"],
            "kwargs_types": {"number": int},
        }

        result = self.handler.process_command(mock_command, ["not_a_number"])

        self.assertIn("invalide", result["text"])

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    def test_process_command_success(self, mock_registry):
        """Test le traitement réussi d'une commande."""
        mock_command = Mock(spec=Command)
        mock_command.value = "/bonjour"

        def mock_bonjour():
            return {"text": "Bonjour!"}

        mock_registry.get.return_value = {"action": Mock(__name__="bonjour"), "arg_names": [], "kwargs_types": {}}

        self.handler.bonjour = mock_bonjour
        result = self.handler.process_command(mock_command, [])

        self.assertEqual(result["text"], "Bonjour!")

    def test_bonjour_method(self):
        """Test la méthode bonjour par défaut."""
        result = self.handler.bonjour()

        self.assertIn("text", result)
        self.assertIn("reply_markup", result)
        self.assertIn("TelegramHandler", result["text"])

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    def test_help_command(self, mock_registry):
        """Test la commande help."""
        mock_menu1 = Mock()
        mock_menu1.value = "/menu1"
        mock_menu2 = Mock()
        mock_menu2.value = "/menu"

        mock_registry.items.return_value = [
            ("/cmd1", {"menu": mock_menu1, "description": "Description 1"}),
            ("/cmd2", {"menu": mock_menu2, "description": "Description 2"}),
            ("/cmd3", {"menu": None, "description": "Description 3"}),
        ]

        result = TelegramHandler.help()

        self.assertIn("text", result)
        self.assertIn("parse_mode", result)
        self.assertEqual(result["parse_mode"], "Markdown")
        self.assertIn("/menu1", result["text"])
        self.assertNotIn("/menu ", result["text"])  # Exclu car c'est "/menu"

    @patch("venantvr.telegram.handler.COMMAND_REGISTRY")
    @patch("venantvr.telegram.handler.logger")
    def test_help_command_error(self, mock_logger, mock_registry):
        """Test la gestion d'erreur dans la commande help."""
        mock_registry.items.side_effect = Exception("Test error")

        result = TelegramHandler.help()

        self.assertIn("Erreur", result["text"])
        mock_logger.error.assert_called()


class TestHandlerIntegration(unittest.TestCase):
    """Tests d'intégration pour le handler."""

    def test_custom_handler_inheritance(self):
        """Test qu'un handler personnalisé peut hériter de TelegramHandler."""

        class CustomHandler(TelegramHandler):
            @staticmethod
            def custom_command(name: str) -> dict:
                return {"text": f"Custom: {name}"}

        handler = CustomHandler()
        self.assertIsInstance(handler, TelegramHandler)

        # Test qu'on peut appeler la méthode personnalisée
        result = handler.custom_command("test")
        self.assertEqual(result["text"], "Custom: test")

        # Test que les méthodes de base fonctionnent toujours
        result = handler.bonjour()
        self.assertIn("CustomHandler", result["text"])


if __name__ == "__main__":
    unittest.main()
