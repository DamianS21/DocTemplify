from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import Dict, Any, List, Tuple
from .google_fonts import GOOGLE_DOCS_FONTS
from .exceptions import GoogleAPIError
from .template_parser import TemplateParser, InvalidTemplateException

GDOCS_DEFAULT_URL = "https://docs.google.com/document/d/{}/edit"

class GoogleDocsConnector:
    def __init__(self, service_account_file: str):
        self.SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        self.GOOGLE_DOCS_FONTS = GOOGLE_DOCS_FONTS
        try:
            
            self.creds = Credentials.from_service_account_file(service_account_file, scopes=self.SCOPES)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            self.template_parser = TemplateParser(self)
        except Exception as e:
            raise GoogleAPIError(f"Failed to initialize Google API services: {str(e)}")

    def create_document(self, title: str, public: bool = False) -> Tuple[str, str]:
        """
        Create a new Google Docs document.

        Args:
            title (str): The title of the new document.
            public (bool): Whether to make the document public.

        Returns:
            Tuple[str, str]: The document ID and URL.
        """
        try:
            body = {
                'title': title
            }
            doc = self.docs_service.documents().create(body=body).execute()
            doc_id = doc['documentId']
            doc_url = GDOCS_DEFAULT_URL.format(doc_id)

            if public:
                self.set_public_permissions(doc_id)

            return doc_id, doc_url
        except Exception as e:
            raise GoogleAPIError(f"Failed to create document: {str(e)}")

    def add_text(self, doc_id: str, text: str, style: Dict[str, Any] = None) -> None:
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': text + '\n'
                }
            }
        ]
        if style:
            requests.append(self._create_style_request(style, 1, len(text) + 1))
        self._batch_update(doc_id, requests)

    def add_heading(self, doc_id: str, text: str, level: int, style: Dict[str, Any] = None) -> None:
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': text + '\n'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text) + 2},
                    'paragraphStyle': {'namedStyleType': f'HEADING_{level}'},
                    'fields': 'namedStyleType'
                }
            }
        ]
        if style:
            requests.append(self._create_style_request(style, 1, len(text) + 1))
        self._batch_update(doc_id, requests)


    def add_list(self, doc_id: str, items: List[str], style: Dict[str, Any] = None) -> None:
        requests = []
        start_index = 1
        for item in items:
            requests.extend([
                {
                    'insertText': {
                        'location': {'index': start_index},
                        'text': item + '\n'
                    }
                },
                {
                    'createParagraphBullets': {
                        'range': {'startIndex': start_index, 'endIndex': start_index + len(item) + 1},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                }
            ])
            if style:
                requests.append(self._create_style_request(style, start_index, start_index + len(item)))
            start_index += len(item) + 1
        self._batch_update(doc_id, requests)

    def add_table(self, doc_id: str, rows: int, cols: int, content: List[List[str]], style: Dict[str, Any] = None) -> None:
        requests = [
            {
                'insertTable': {
                    'rows': rows,
                    'columns': cols,
                    'location': {'index': 1}
                }
            }
        ]
        self._batch_update(doc_id, requests)

        for i, row in enumerate(content):
            for j, cell in enumerate(row):
                self.add_text(doc_id, cell, style)


    def add_image_placeholder(self, doc_id: str, placeholder: str, style: Dict[str, Any] = None) -> None:
        self.add_text(doc_id, placeholder, style)

    def _batch_update(self, doc_id: str, requests: List[Dict[str, Any]]) -> None:
        try:
            self.docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        except Exception as e:
            raise GoogleAPIError(f"Failed to update document: {str(e)}")


    def get_document_url(self, document_id: str) -> str:
        """
        Get the URL for a Google Docs document.

        Args:
            document_id (str): The ID of the document.

        Returns:
            str: The URL of the document.
        """
        return GDOCS_DEFAULT_URL.format(document_id)

    def get_document_text(self, document_id: str) -> str:
        try:
            document = self.docs_service.documents().get(documentId=document_id).execute()
            content = document.get('body').get('content')
            return self._extract_text_from_content(content)
        except Exception as e:
            raise GoogleAPIError(f"Failed to get document text: {str(e)}")

    def _extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        text = ''
        for element in content:
            if 'paragraph' in element:
                text += self._extract_text_from_paragraph(element['paragraph'])
            elif 'table' in element:
                text += self._extract_text_from_table(element['table'])
        return text

    def _extract_text_from_paragraph(self, paragraph: Dict[str, Any]) -> str:
        return ''.join(
            text_element['textRun']['content']
            for text_element in paragraph['elements']
            if 'textRun' in text_element and 'content' in text_element['textRun']
        )

    def _extract_text_from_table(self, table: Dict[str, Any]) -> str:
        text = ''
        for row in table['tableRows']:
            for cell in row['tableCells']:
                for cell_content in cell['content']:
                    if 'paragraph' in cell_content:
                        text += self._extract_text_from_paragraph(cell_content['paragraph'])
        return text

    def validate_template(self, document_id: str, data: Dict[str, Any]) -> None:
        try:
            document_text = self.get_document_text(document_id)
            parameters = self.template_parser.find_parameters(document_text)
            missing_params = []

            for param in parameters:
                if param not in data:
                    missing_params.append(param)
            
            if missing_params:
                raise InvalidTemplateException(f"The following parameters are missing from the data: {', '.join(missing_params)}")
        except Exception as e:
            raise GoogleAPIError(f"Failed to validate template: {str(e)}")


    def replace_placeholders(self, document_id: str, data: Dict[str, Any]) -> None:
        try:
            self.validate_template(document_id, data)
            
            document_text = self.get_document_text(document_id)
            placeholders = self.template_parser.find_parameters(document_text)
            
            for placeholder_full in placeholders:
                placeholder = placeholder_full.split(':')[0].strip()
                style = placeholder_full.split(':')[1].strip() if ':' in placeholder_full else None

                value = self._extract_value_with_dot_notation(data, placeholder)
                
                if isinstance(value, dict):
                    if 'value' in value:
                        text_value = str(value['value'])
                        style = value.get('style', style)
                    else:
                        raise InvalidTemplateException(f"Invalid value for placeholder '{placeholder}'. Expected a string or a dict with 'value' key.")
                else:
                    text_value = str(value)

                # Replace the placeholder with the text value
                replace_request = {
                    'replaceAllText': {
                        'containsText': {
                            'text': '{{' + placeholder_full + '}}',
                            'matchCase': True,
                        },
                        'replaceText': text_value,
                    }
                }
                
                replace_result = self.docs_service.documents().batchUpdate(
                    documentId=document_id, 
                    body={'requests': [replace_request]}
                ).execute()

                # Check if any replacements were made
                if 'replaceAllText' in replace_result['replies'][0]:
                    replaces = replace_result['replies'][0]['replaceAllText'].get('occurrencesChanged', 0)
                    if replaces > 0 and style:
                        # Get the updated document to find the location of the replaced text
                        updated_document = self.docs_service.documents().get(documentId=document_id).execute()
                        start_index, end_index = self._find_text_range(updated_document, text_value)

                        if start_index is not None and end_index is not None:
                            # Parse the style string into a dictionary
                            style_dict = self.template_parser._parse_css_style(style)

                            # Apply styling to the replaced text
                            style_request = self._create_style_request(style_dict, start_index, end_index)
                            if style_request:
                                self.docs_service.documents().batchUpdate(
                                    documentId=document_id, 
                                    body={'requests': [style_request]}
                                ).execute()
                        else:
                            print(f"Warning: Unable to find the replaced text '{text_value}' in the document.")
                    elif replaces == 0:
                        print(f"Warning: Placeholder '{placeholder_full}' not found in the document.")
                else:
                    print(f"Warning: Failed to replace placeholder '{placeholder_full}' in the document.")

        except Exception as e:
            raise GoogleAPIError(f"Failed to replace placeholders: {str(e)}")

    def _find_text_range(self, document: Dict[str, Any], text: str) -> Tuple[int, int]:
        """Find the start and end indices of a specific text in the document."""
        content = document.get('body', {}).get('content', [])
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        content = text_run['textRun'].get('content', '')
                        start = content.find(text)
                        if start != -1:
                            return text_run['startIndex'] + start, text_run['startIndex'] + start + len(text)
        return None, None

    def _create_style_request(self, style_dict: Dict[str, str], start_index: int, end_index: int) -> Dict[str, Any]:
        """Create a style request for the Google Docs API based on CSS-like styles."""
        text_style = {}
        fields = []

        if 'color' in style_dict:
            text_style['foregroundColor'] = self._parse_color(style_dict['color'])
            fields.append('foregroundColor')

        if 'background-color' in style_dict:
            text_style['backgroundColor'] = self._parse_color(style_dict['background-color'])
            fields.append('backgroundColor')

        if 'font-weight' in style_dict:
            text_style['bold'] = style_dict['font-weight'].lower() == 'bold'
            fields.append('bold')

        if 'font-style' in style_dict:
            text_style['italic'] = style_dict['font-style'].lower() == 'italic'
            fields.append('italic')

        if 'text-decoration' in style_dict:
            if 'underline' in style_dict['text-decoration'].lower():
                text_style['underline'] = True
                fields.append('underline')
            if 'line-through' in style_dict['text-decoration'].lower():
                text_style['strikethrough'] = True
                fields.append('strikethrough')

        if 'font-size' in style_dict:
            size = style_dict['font-size'].lower()
            if size.endswith('px'):
                magnitude = float(size[:-2])
            elif size.endswith('pt'):
                magnitude = float(size[:-2])
            else:
                try:
                    magnitude = float(size)
                except ValueError:
                    magnitude = 11  # default size
            text_style['fontSize'] = {'magnitude': magnitude, 'unit': 'PT'}
            fields.append('fontSize')

        if 'font-family' in style_dict:
            font = style_dict['font-family'].strip("'\"")
            if font in GOOGLE_DOCS_FONTS:
                text_style['weightedFontFamily'] = {'fontFamily': font}
                fields.append('weightedFontFamily')
            else:
                print(f"Warning: Font '{font}' is not available in Google Docs. Using default font.")

        if text_style:
            return {
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'textStyle': text_style,
                    'fields': ','.join(fields)
                }
            }
        return None

    def _parse_color(self, color: str) -> Dict[str, Any]:
        """Parse a color string into a Google Docs API color object."""
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16) / 255, int(color[3:5], 16) / 255, int(color[5:7], 16) / 255
        elif color.startswith('rgb'):
            r, g, b = map(lambda x: int(x.strip()) / 255, color[4:-1].split(','))
        else:
            r, g, b = 0, 0, 0

        return {
            'color': {
                'rgbColor': {
                    'red': r,
                    'green': g,
                    'blue': b
                }
            }
        }

    def _extract_value_with_dot_notation(self, data: Dict[str, Any], key: str) -> Any:
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                if k in value:
                    value = value[k]
                else:
                    return None  # or raise an exception if you prefer
            else:
                return None  # or raise an exception if you prefer
        return value


    def copy_template(self, template_id: str, new_name: str = 'Generated Document') -> str:
        try:
            copied_file = {'name': new_name}
            new_doc = self.drive_service.files().copy(fileId=template_id, body=copied_file).execute()
            return new_doc['id']
        except Exception as e:
            raise GoogleAPIError(f"Failed to copy template: {str(e)}")

    def set_public_permissions(self, document_id: str) -> None:
        """
        Set public permissions for the document.

        Args:
            document_id (str): The ID of the document to make public.
        """
        try:
            self.drive_service.permissions().create(
                fileId=document_id,
                body={'type': 'anyone', 'role': 'writer'},
                fields='id'
            ).execute()
        except Exception as e:
            raise GoogleAPIError(f"Failed to set public permissions: {str(e)}")