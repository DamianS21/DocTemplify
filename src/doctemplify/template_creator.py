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
                print(f"Processing {key}: {value}")  # Debug log
                self._add_element(doc_id, key, value)

            return doc_id, doc_url
        except Exception as e:
            raise TemplateCreationError(f"Failed to create template: {str(e)}")

    def _add_element(self, doc_id: str, key: str, element: Dict[str, Any]) -> None:
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

            # Debug log
            print(f"Adding table with {rows} rows and {cols} cols")
            for row in table_content:
                print(f"Row: {row}")  # Log each row to verify the content

            # Ensure the table content is formatted correctly as rows and cells
            if table_content and isinstance(table_content[0], str):
                table_content = [table_content]

            # Process each row and column
            processed_table_content = []
            for row in table_content:
                processed_row = []
                for cell in row:
                    processed_row.append(cell)  # Add each cell to the row
                processed_table_content.append(processed_row)

            # Now pass the processed table content to the connector
            # Ensure that the connector adds table rows correctly
            self.connector.add_table(doc_id, rows, cols, processed_table_content, style)
        elif element_type == 'image':
            self.connector.add_image_placeholder(doc_id, content, style)
        else:
            raise ValueError(f"Unknown element type: {element_type}")