# test_summary_generation.py

import unittest
from src.summarizer import process_talk_pdfs, TalkContent, Summary
from unittest.mock import patch, mock_open

class TestSummaryGeneration(unittest.TestCase):

    @patch('src.summarizer.read_pdf')
    @patch('src.summarizer.get_ollama_summary')
    def test_process_talk_pdfs(self, mock_get_summary, mock_read_pdf):
        # Test processing of multiple PDF files
        mock_read_pdf.return_value = TalkContent(text="Test content", metadata={})
        mock_get_summary.return_value = Summary(
            title="Test Title",
            main_points=["Point 1"],
            technical_details=["Detail 1"],
            implications=["Implication 1"]
        )

        with patch('os.listdir', return_value=['test1.pdf', 'test2.pdf']):
            with patch('builtins.open', mock_open()) as mock_file:
                process_talk_pdfs("/fake/path", "/fake/output", "Test prompt")

        self.assertEqual(mock_read_pdf.call_count, 2)
        self.assertEqual(mock_get_summary.call_count, 2)

    def test_empty_directory_handling(self):
        # Test handling of an empty directory
        with patch('os.listdir', return_value=[]):
            result = process_talk_pdfs("/fake/path", "/fake/output", "Test prompt")
        self.assertIsNone(result)

    @patch('src.summarizer.read_pdf')
    @patch('src.summarizer.get_ollama_summary')
    def test_error_handling_during_processing(self, mock_get_summary, mock_read_pdf):
        # Test error handling during PDF processing
        mock_read_pdf.side_effect = Exception("PDF Error")
        mock_get_summary.return_value = Summary(
            title="Error",
            main_points=[],
            technical_details=[],
            implications=[]
        )

        with patch('os.listdir', return_value=['test1.pdf']):
            with patch('builtins.open', mock_open()) as mock_file:
                process_talk_pdfs("/fake/path", "/fake/output", "Test prompt")

        self.assertEqual(mock_get_summary.call_count, 0)

    def test_prompt_template_usage(self):
        # Test correct usage of the prompt template
        # This would involve mocking the template reading and verifying its content in the API call
        pass
