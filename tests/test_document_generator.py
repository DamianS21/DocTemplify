import unittest
from unittest.mock import MagicMock
from doctemplify import DocumentGenerator
from doctemplify.exceptions import DocumentGenerationError

class TestDocumentGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_connector = MagicMock()
        self.generator = DocumentGenerator(self.mock_connector)

    def test_generate_document_success(self):
        self.mock_connector.copy_template.return_value = 'new_doc_id'
        
        result = self.generator.generate_document('template_id', {'name': 'John'})
        
        self.assertEqual(result, 'new_doc_id')
        self.mock_connector.copy_template.assert_called_once()
        self.mock_connector.replace_placeholders.assert_called_once()
        self.mock_connector.set_public_permissions.assert_called_once()

    def test_generate_document_failure(self):
        self.mock_connector.copy_template.side_effect = Exception('Copy failed')

        with self.assertRaises(DocumentGenerationError):
            self.generator.generate_document('template_id', {'name': 'John'})