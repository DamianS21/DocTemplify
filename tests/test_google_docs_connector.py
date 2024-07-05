import unittest
from unittest.mock import MagicMock, patch
from doctemplify import GoogleDocsConnector
from doctemplify.exceptions import GoogleAPIError

class TestGoogleDocsConnector(unittest.TestCase):
    @patch('doctemplify.google_docs_connector.Credentials')
    @patch('doctemplify.google_docs_connector.build')
    def setUp(self, mock_build, mock_credentials):
        self.mock_credentials = mock_credentials
        self.mock_build = mock_build
        self.connector = GoogleDocsConnector('fake_service_account.json')

    def test_get_document_text(self):
        mock_document = {
            'body': {
                'content': [
                    {'paragraph': {'elements': [{'textRun': {'content': 'Test content'}}]}}
                ]
            }
        }
        self.connector.docs_service.documents().get().execute.return_value = mock_document
        
        result = self.connector.get_document_text('fake_doc_id')
        self.assertEqual(result, 'Test content')

    def test_replace_placeholders(self):
        self.connector.get_document_text = MagicMock(return_value='Hello {{name}}')
        mock_batch_update = MagicMock()
        self.connector.docs_service.documents().batchUpdate = mock_batch_update

        self.connector.replace_placeholders('fake_doc_id', {'name': 'John'})

        mock_batch_update.assert_called_once_with(
            documentId='fake_doc_id',
            body={'requests': [{'replaceAllText': {'containsText': {'text': '{{name}}', 'matchCase': True}, 'replaceText': 'John'}}]}
        )

    def test_copy_template(self):
        self.connector.drive_service.files().copy().execute.return_value = {'id': 'new_doc_id'}

        result = self.connector.copy_template('template_id')
        self.assertEqual(result, 'new_doc_id')

    def test_set_public_permissions(self):
        mock_create = MagicMock()
        self.connector.drive_service.permissions().create = mock_create

        self.connector.set_public_permissions('fake_doc_id')

        mock_create.assert_called_once_with(
            fileId='fake_doc_id',
            body={'type': 'anyone', 'role': 'writer'},
            fields='id'
        )

    def test_google_api_error(self):
        self.connector.docs_service.documents().get().execute.side_effect = Exception('API Error')

        with self.assertRaises(GoogleAPIError):
            self.connector.get_document_text('fake_doc_id')