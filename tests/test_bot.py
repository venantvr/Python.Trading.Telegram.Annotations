"""Tests unitaires pour le module TelegramBot."""

import unittest
from unittest.mock import Mock, patch
import queue

from venantvr.telegram.bot import TelegramBot
from venantvr.telegram.handler import TelegramHandler


class TestTelegramBot(unittest.TestCase):
    """Tests pour la classe TelegramBot."""

    def setUp(self) -> None:
        """Initialisation avant chaque test."""
        self.bot_token = "test_token_12345"
        self.chat_id = "123456789"
        self.handler = Mock(spec=TelegramHandler)
        
    @patch('venantvr.telegram.bot.threading.Thread')
    def test_bot_initialization(self, _mock_thread):
        """Test l'initialisation correcte du bot."""
        bot = TelegramBot(self.bot_token, self.chat_id, self.handler)  # type: ignore[arg-type]
        
        self.assertEqual(bot.api_url, f"https://api.telegram.org/bot{self.bot_token}")
        self.assertEqual(bot.chat_id, self.chat_id)
        self.assertIsInstance(bot.incoming_queue, queue.Queue)
        self.assertIsInstance(bot.outgoing_queue, queue.Queue)
        self.assertEqual(len(bot.handlers), 1)
        self.assertEqual(bot.handlers[0], self.handler)
        
    def test_single_handler_conversion(self):
        """Test que un handler unique est converti en liste."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id, self.handler)  # type: ignore[arg-type]
            self.assertIsInstance(bot.handlers, list)
            self.assertEqual(len(bot.handlers), 1)
            
    def test_multiple_handlers(self):
        """Test avec plusieurs handlers."""
        handler2 = Mock(spec=TelegramHandler)
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id, [self.handler, handler2])  # type: ignore[arg-type]
            self.assertEqual(len(bot.handlers), 2)
            
    @patch('venantvr.telegram.bot.requests.Session')
    def test_session_creation(self, mock_session):
        """Test la création de la session HTTP avec retry."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            TelegramBot(self.bot_token, self.chat_id)
            mock_session.assert_called()
            
    def test_build_menu_keyboard_invalid_menu(self):
        """Test la construction d'un menu avec une valeur invalide."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id)
            with patch('venantvr.telegram.classes.menu.Menu.from_value', side_effect=ValueError("Invalid menu")):
                result = bot._build_menu_keyboard("invalid_menu")
                self.assertIn("Erreur", result["text"])
                
    @patch('venantvr.telegram.bot.COMMAND_REGISTRY')
    def test_build_menu_keyboard_valid(self, mock_registry):
        """Test la construction d'un menu valide."""
        mock_menu = Mock()
        mock_menu.value = "/test_menu"
        mock_registry.values.return_value = [
            {'menu': mock_menu, 'enum': Mock(name="TEST", value="/test")}
        ]
        
        with patch('venantvr.telegram.bot.threading.Thread'):
            with patch('venantvr.telegram.classes.menu.Menu.from_value', return_value=mock_menu):
                bot = TelegramBot(self.bot_token, self.chat_id)
                result = bot._build_menu_keyboard("/test_menu")
                
                self.assertIn("text", result)
                self.assertIn("reply_markup", result)
                self.assertIn("inline_keyboard", result["reply_markup"])
                
    def test_send_message_dict(self):
        """Test l'envoi d'un message unique."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id)
            message = {"text": "Test message", "chat_id": self.chat_id}
            bot.send_message(message)
            
            self.assertFalse(bot.outgoing_queue.empty())
            sent_message = bot.outgoing_queue.get()
            self.assertEqual(sent_message, message)
            
    def test_send_message_list(self):
        """Test l'envoi de plusieurs messages."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id)
            messages = [
                {"text": "Message 1", "chat_id": self.chat_id},
                {"text": "Message 2", "chat_id": self.chat_id}
            ]
            bot.send_message(messages)
            
            self.assertEqual(bot.outgoing_queue.qsize(), 2)
            
    def test_send_message_invalid_type(self):
        """Test l'envoi avec un type invalide."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            with patch('venantvr.telegram.bot.logger') as mock_logger:
                bot = TelegramBot(self.bot_token, self.chat_id)
                # Test avec une string au lieu d'un dict/list - type: ignore pour le test
                bot.send_message("invalid_type")  # type: ignore
                mock_logger.warning.assert_called_once()
                
    def test_stop_bot(self):
        """Test l'arrêt propre du bot."""
        with patch('venantvr.telegram.bot.threading.Thread'):
            bot = TelegramBot(self.bot_token, self.chat_id)
            bot._session = Mock()
            bot.stop()
            
            # Vérifier que les signaux d'arrêt sont envoyés
            self.assertEqual(bot.outgoing_queue.get(), None)
            self.assertEqual(bot.incoming_queue.get(), None)
            bot._session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()