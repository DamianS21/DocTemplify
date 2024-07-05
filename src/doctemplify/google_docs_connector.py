from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from .exceptions import GoogleAPIError
from .utils import extract_value_with_dot_notation
import re

class GoogleDocsConnector:
    def __init__(self, service_account_file):
        self.SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        try:
            self.creds = Credentials.from_service_account_file(service_account_file, scopes=self.SCOPES)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
        except Exception as e:
            raise GoogleAPIError(f"Failed to initialize Google API services: {str(e)}")

    def get_document_text(self, document_id):
        try:
            document = self.docs_service.documents().get(documentId=document_id).execute()
            content = document.get('body').get('content')
            return self._extract_text_from_content(content)
        except Exception as e:
            raise GoogleAPIError(f"Failed to get document text: {str(e)}")

    def _extract_text_from_content(self, content):
        text = ''
        for element in content:
            if 'paragraph' in element:
                text += self._extract_text_from_paragraph(element['paragraph'])
            elif 'table' in element:
                text += self._extract_text_from_table(element['table'])
        return text

    def _extract_text_from_paragraph(self, paragraph):
        return ''.join(
            text_element['textRun']['content']
            for text_element in paragraph['elements']
            if 'textRun' in text_element and 'content' in text_element['textRun']
        )

    def _extract_text_from_table(self, table):
        text = ''
        for row in table['tableRows']:
            for cell in row['tableCells']:
                for cell_content in cell['content']:
                    if 'paragraph' in cell_content:
                        text += self._extract_text_from_paragraph(cell_content['paragraph'])
        return text

    def replace_placeholders(self, document_id, data):
        try:
            document_text = self.get_document_text(document_id)
            placeholders = re.findall(r'\{\{(.*?)\}\}', document_text)
            
            for placeholder in placeholders:
                value = extract_value_with_dot_notation(data, placeholder)
                requests = [{
                    'replaceAllText': {
                        'containsText': {
                            'text': '{{' + placeholder + '}}',
                            'matchCase': True,
                        },
                        'replaceText': str(value),
                    }
                }]
                self.docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        except Exception as e:
            raise GoogleAPIError(f"Failed to replace placeholders: {str(e)}")

    def copy_template(self, template_id, new_name='Generated Document'):
        try:
            copied_file = {'name': new_name}
            new_doc = self.drive_service.files().copy(fileId=template_id, body=copied_file).execute()
            return new_doc['id']
        except Exception as e:
            raise GoogleAPIError(f"Failed to copy template: {str(e)}")

    def set_public_permissions(self, document_id):
        try:
            self.drive_service.permissions().create(
                fileId=document_id,
                body={'type': 'anyone', 'role': 'writer'},
                fields='id'
            ).execute()
        except Exception as e:
            raise GoogleAPIError(f"Failed to set public permissions: {str(e)}")