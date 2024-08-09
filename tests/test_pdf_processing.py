# test_pdf_processing.py

import unittest
import tempfile
import os
from src.summarizer import read_pdf, TalkContent

class TestPDFProcessing(unittest.TestCase):

    def test_valid_pdf_reading(self):
        # Test reading a valid PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(b"%PDF-1.3\n%Test PDF content")
            temp_pdf.flush()

            result = read_pdf(temp_pdf.name)
            os.unlink(temp_pdf.name)

        self.assertIsInstance(result, TalkContent)
        self.assertIn("Test PDF content", result.text)

    def test_invalid_pdf_handling(self):
        # Test handling of invalid PDF files
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(b"This is not a valid PDF")
            temp_pdf.flush()

            with self.assertRaises(Exception):
                read_pdf(temp_pdf.name)

            os.unlink(temp_pdf.name)

    def test_nonexistent_file_handling(self):
        # Test handling of non-existent files
        with self.assertRaises(FileNotFoundError):
            read_pdf("nonexistent_file.pdf")

    def test_metadata_extraction(self):
        # Test extraction of metadata from PDF
        # This would require creating a PDF with known metadata
        pass

