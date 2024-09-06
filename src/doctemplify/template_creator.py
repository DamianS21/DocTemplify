from typing import Dict, Any, List, Tuple
from .google_docs_connector import GoogleDocsConnector
from .exceptions import TemplateCreationError

class TemplateCreator:
    def __init__(self, google_docs_connector: GoogleDocsConnector):
        self.connector = google_docs_connector

    def create_template_from_json(self, json_structure: Dict[str, Any], document_title: str, public: bool = False) -> Tuple[str, str]:
        try:
            # Reset the current_index before creating a new template
            self.connector.current_index = 1
            
            # Create a new document
            doc_id, doc_url = self.connector.create_document(document_title, public)

            # Process the JSON structure and add content to the document in order
            for key, value in json_structure.items():
                self._add_element(doc_id, key, value)

            return doc_id, doc_url
        except Exception as e:
            raise TemplateCreationError(f"Failed to create template: {str(e)}")

    def _add_element(self, doc_id: str, key: str, element: Dict[str, Any]) -> None:
        """
        Add an element to the document based on its type.

        Args:
            doc_id (str): The ID of the document being created.
            key (str): The key of the element in the JSON structure.
            element (Dict[str, Any]): The element definition from the JSON structure.
        """
        element_type = element['type']
        content = element.get('content', '')
        style = element.get('style', {})

        if element_type == 'heading':
            level = element.get('level', 1)
            self.connector.add_heading(doc_id, content, level, style)
        elif element_type == 'text':
            self.connector.add_text(doc_id, content, style)
        elif element_type == 'list':
            items = element.get('items', [])
            self.connector.add_list(doc_id, items, style)
        elif element_type == 'table':
            rows = element.get('rows', 2)
            cols = element.get('cols', 2)
            table_content = element.get('content', [])
            self.connector.add_table(doc_id, rows, cols, table_content, style)
        elif element_type == 'image':
            self.connector.add_image_placeholder(doc_id, content, style)
        else:
            raise ValueError(f"Unknown element type: {element_type}")