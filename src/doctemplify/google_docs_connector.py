from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from typing import Dict, Any, List, Tuple, Optional
from .google_fonts import GOOGLE_DOCS_FONTS
from .exceptions import GoogleAPIError
from .template_parser import TemplateParser, InvalidTemplateException
from .oauth_handler import OAuthHandler

GDOCS_DEFAULT_URL = "https://docs.google.com/document/d/{}/edit"

class GoogleDocsConnector:
    def __init__(self, auth_file: str, auth_type: str = 'service_account'):
        self.SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        self.GOOGLE_DOCS_FONTS = GOOGLE_DOCS_FONTS
        self.auth_type = auth_type
        self.auth_file = auth_file
        self.drive_service = None
        self.docs_service = None
        self.template_parser = None
        self.current_index = 1
        self._initialize_services()

    def _initialize_services(self):
        try:
            if self.auth_type == 'service_account':
                creds = ServiceAccountCredentials.from_service_account_file(self.auth_file, scopes=self.SCOPES)
            elif self.auth_type == 'oauth':
                oauth_handler = OAuthHandler(self.auth_file, self.SCOPES)
                creds = oauth_handler.get_credentials()
            else:
                raise ValueError(f"Invalid auth_type: {self.auth_type}. Must be 'service_account' or 'oauth'.")

            self.drive_service = build('drive', 'v3', credentials=creds)
            self.docs_service = build('docs', 'v1', credentials=creds)
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

            self.current_index = 1
            return doc_id, doc_url
        except Exception as e:
            raise GoogleAPIError(f"Failed to create document: {str(e)}")

    def add_text(self, doc_id: str, text: str, style: Dict[str, Any] = None) -> None:
        requests = [
            {
                'insertText': {
                    'location': {'index': self.current_index},
                    'text': text + '\n'
                }
            }
        ]
        if style:
            requests.append(self._create_style_request(style, self.current_index, self.current_index + len(text)))
        self._batch_update(doc_id, requests)
        self.current_index += len(text) + 1

    def add_heading(self, doc_id: str, text: str, level: int, style: Dict[str, Any] = None) -> None:
        requests = [
            {
                'insertText': {
                    'location': {'index': self.current_index},
                    'text': text + '\n'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': self.current_index, 'endIndex': self.current_index + len(text) + 1},
                    'paragraphStyle': {'namedStyleType': f'HEADING_{level}'},
                    'fields': 'namedStyleType'
                }
            }
        ]
        if style:
            requests.append(self._create_style_request(style, self.current_index, self.current_index + len(text)))
        self._batch_update(doc_id, requests)
        self.current_index += len(text) + 1 


    def add_list(self, doc_id: str, items: List[str], style: Dict[str, Any] = None) -> None:
        requests = []
        for item in items:
            requests.extend([
                {
                    'insertText': {
                        'location': {'index': self.current_index},
                        'text': item + '\n'
                    }
                },
                {
                    'createParagraphBullets': {
                        'range': {'startIndex': self.current_index, 'endIndex': self.current_index + len(item) + 1},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                }
            ])
            if style:
                requests.append(self._create_style_request(style, self.current_index, self.current_index + len(item)))
            self.current_index += len(item) + 1  # Update the current index for each item
        self._batch_update(doc_id, requests)

    def add_table(self, doc_id: str, rows: int, cols: int, content: List[List[str]], style: Dict[str, Any] = None) -> None:
        # Insert an empty table
        requests = [{
            'insertTable': {
                'rows': rows,
                'columns': cols,
                'location': {
                    'index': self.current_index
                }
            }
        }]

        self._batch_update(doc_id, requests)

        # Get the updated document to find the table start index
        document = self.docs_service.documents().get(documentId=doc_id).execute()
        table_index = self._find_last_table_index(document)

        if table_index is None:
            raise GoogleAPIError("Failed to find the newly created table.")

        # Insert content into each cell
        for row_index in range(rows):
            for col_index in range(cols):
                cell_content = content[row_index][col_index] if row_index < len(content) and col_index < len(content[row_index]) else ''
                
                # Refresh the document after each row to ensure correct indices for the next row
                document = self.docs_service.documents().get(documentId=doc_id).execute()
                cell_start_index = self._find_cell_start_index(document, table_index, row_index, col_index)
                
                if cell_start_index is not None:
                    self._insert_text_into_cell(doc_id, cell_start_index, cell_content, style)

        # Update the current index to after the table
        document = self.docs_service.documents().get(documentId=doc_id).execute()
        self.current_index = self._find_table_end_index(document, table_index)


    def _find_last_table_index(self, document: Dict[str, Any]) -> Optional[int]:
        for i, element in enumerate(reversed(document.get('body', {}).get('content', []))):
            if 'table' in element:
                return len(document['body']['content']) - i - 1
        return None

    def _find_cell_start_index(self, document: Dict[str, Any], table_index: int, row_index: int, col_index: int) -> Optional[int]:
        table = document['body']['content'][table_index]['table']
        if row_index < len(table['tableRows']) and col_index < len(table['tableRows'][row_index]['tableCells']):
            cell_content = table['tableRows'][row_index]['tableCells'][col_index]['content']
            return cell_content[0]['startIndex'] if cell_content else None
        return None

    def _find_table_end_index(self, document: Dict[str, Any], table_index: int) -> int:
        return document['body']['content'][table_index].get('endIndex', self.current_index)
    
    def _find_last_table_index(self, document: Dict[str, Any]) -> Optional[int]:
        for i, element in enumerate(reversed(document.get('body', {}).get('content', []))):
            if 'table' in element:
                return len(document['body']['content']) - i - 1
        return None

    def _insert_text_into_cell(self, doc_id: str, start_index: int, text: str, style: Dict[str, Any] = None) -> None:
        """
        Insert text into a table cell by specifying the start index of the cell.
        
        Args:
            doc_id (str): The ID of the document.
            start_index (int): The start index where text will be inserted.
            text (str): The text to insert into the cell.
            style (Dict[str, Any]): Optional styling for the inserted text.
        """
        requests = [{
            'insertText': {
                'location': {
                    'index': start_index
                },
                'text': text
            }
        }]

        if style:
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': start_index + len(text)
                    },
                    'textStyle': self._create_text_style(style),
                    'fields': 'foregroundColor,backgroundColor,bold,italic,underline,strikethrough,fontSize,weightedFontFamily'
                }
            })

        self._batch_update(doc_id, requests)

    def _create_text_style(self, style: Dict[str, Any]) -> Dict[str, Any]:
        text_style = {}
        if 'color' in style:
            text_style['foregroundColor'] = self._parse_color(style['color'])
        if 'background-color' in style:
            text_style['backgroundColor'] = self._parse_color(style['background-color'])
        if 'font-weight' in style:
            text_style['bold'] = style['font-weight'].lower() == 'bold'
        if 'font-style' in style:
            text_style['italic'] = style['font-style'].lower() == 'italic'
        if 'text-decoration' in style:
            if 'underline' in style['text-decoration'].lower():
                text_style['underline'] = True
            if 'line-through' in style['text-decoration'].lower():
                text_style['strikethrough'] = True
        if 'font-size' in style:
            size = style['font-size'].lower()
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
        if 'font-family' in style:
            font = style['font-family'].strip("'\"")
            if font in self.GOOGLE_DOCS_FONTS:
                text_style['weightedFontFamily'] = {'fontFamily': font}
        return text_style

    def _find_table_start_index(self, document: Dict[str, Any], after_index: int) -> Optional[int]:
        for element in document.get('body', {}).get('content', []):
            if 'table' in element and element.get('startIndex', 0) > after_index:
                return element.get('startIndex')
        return None

    def _find_cell_location(self, document: Dict[str, Any], table_start_index: int, row_index: int, col_index: int) -> Optional[int]:
        for element in document.get('body', {}).get('content', []):
            if 'table' in element and element.get('startIndex') == table_start_index:
                table = element['table']
                if row_index < len(table['tableRows']) and col_index < len(table['tableRows'][row_index]['tableCells']):
                    cell = table['tableRows'][row_index]['tableCells'][col_index]
                    return cell['content'][0]['startIndex']
        return None

    def add_image(self, doc_id: str, image_url: str, width: int, height: int) -> None:
        """
        Add an image to the document at the current index.

        Args:
            doc_id (str): The ID of the document.
            image_url (str): The URL of the image to insert.
            width (int): The width of the image in points (PT).
            height (int): The height of the image in points (PT).
        """
        requests = [{
            'insertInlineImage': {
                'uri': image_url,
                'location': {
                    'index': self.current_index
                },
                'objectSize': {
                    'width': {'magnitude': width, 'unit': 'PT'},
                    'height': {'magnitude': height, 'unit': 'PT'}
                }
            }
        }]

        self._batch_update(doc_id, requests)

        # Move index after image
        self.current_index += 1


    def add_image_placeholder(self, doc_id: str, placeholder: str, style: Dict[str, Any] = None) -> None:
        """
        Add an image placeholder to the document at the current index.

        Args:
            doc_id (str): The ID of the document.
            placeholder (str): The text placeholder to be replaced later with the image.
            style (Dict[str, Any], optional): Optional styling for the placeholder text.
        """
        self.add_text(doc_id, placeholder, style)


    def _batch_update(self, doc_id: str, requests: List[Dict[str, Any]]) -> None:
        try:
            self.docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        except Exception as e:
            print(f"Error in batch update: {str(e)}")
            print(f"Requests that caused the error: {requests}")
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
                if placeholder.startswith("IMAGE_PLACEHOLDER"):
                    image_key = placeholder_full.split(':')[1].strip()
                    image_data = data.get(f"IMAGE_PLACEHOLDER:{image_key}")
                    if image_data and isinstance(image_data, dict):
                        image_url = image_data.get('url')
                        width = image_data.get('width', 600)  # Default width
                        height = image_data.get('height', 400)  # Default height
                        if image_url:
                            self._replace_image_placeholder(document_id, placeholder_full, image_url, width, height)
                    continue  # Skip to the next placeholder if it was an image

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

    def _replace_image_placeholder(self, document_id: str, placeholder: str, image_url: str, width: int, height: int) -> None:
        # Find the start and end index of the placeholder text
        start_index, end_index = self._find_text_range(self.docs_service.documents().get(documentId=document_id).execute(), '{{' + placeholder + '}}')

        if start_index is not None and end_index is not None:
            # First, delete the placeholder from the document
            self._batch_update(document_id, [{'deleteContentRange': {'range': {'startIndex': start_index, 'endIndex': end_index}}}])

            # Refresh the document to get the updated content and accurate index after deletion
            document = self.docs_service.documents().get(documentId=document_id).execute()

            # Calculate the correct index to insert the image
            image_insert_index = self._find_text_range(document, '')[0] if start_index is None else start_index

            # Now, insert the image at the correct index
            requests = [{
                'insertInlineImage': {
                    'uri': image_url,
                    'location': {
                        'index': image_insert_index
                    },
                    'objectSize': {
                        'width': {'magnitude': width, 'unit': 'PT'},
                        'height': {'magnitude': height, 'unit': 'PT'}
                    }
                }
            }]

            self._batch_update(document_id, requests)

            # Move the current index to the position after the inserted image
            self.current_index = image_insert_index + 1


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