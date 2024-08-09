# test_ollama_integration.py

import unittest
from unittest.mock import patch, MagicMock
from src.summarizer import get_ollama_summary, TalkContent, Summary

class TestOllamaIntegration(unittest.TestCase):

    @patch('src.summarizer.requests.post')
    def test_successful_api_call(self, mock_post):
        # Test a successful API call to Ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': '{"title": "Test Title", "main_points": ["Point 1"], "technical_details": ["Detail 1"], "implications": ["Implication 1"]}'}
        mock_post.return_value = mock_response

        content = TalkContent(text="Test content", metadata={})
        result = get_ollama_summary(content, "Test prompt")

        self.assertIsInstance(result, Summary)
        self.assertEqual(result.title, "Test Title")

    def test_api_error_handling(self):
        # Test error handling for API calls
        with patch('src.summarizer.requests.post', side_effect=Exception("API Error")):
            content = TalkContent(text="Test content", metadata={})
            with self.assertRaises(Exception):
                get_ollama_summary(content, "Test prompt")

    def test_invalid_response_handling(self):
        # Test handling of invalid API responses
        with patch('src.summarizer.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'response': 'Invalid JSON'}
            mock_post.return_value = mock_response

            content = TalkContent(text="Test content", metadata={})
            result = get_ollama_summary(content, "Test prompt")

            self.assertEqual(result.title, "Error")

