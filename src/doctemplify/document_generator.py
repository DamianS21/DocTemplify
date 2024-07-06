from typing import Dict, Any
from .exceptions import DocumentGenerationError
from .template_parser import InvalidTemplateException
from .google_docs_connector import GoogleDocsConnector

class DocumentGenerator:
    def __init__(self, google_docs_connector: GoogleDocsConnector):
        self.connector = google_docs_connector

    def generate_document(self, template_id: str, data: Dict[str, Any], new_name: str = 'Generated Document') -> str:
        try:
            # Validate the template before copying
            self.connector.validate_template(template_id, data)

            # Copy the template
            new_doc_id = self.connector.copy_template(template_id, new_name)

            # Replace placeholders with data
            self.connector.replace_placeholders(new_doc_id, data)

            # Set public permissions
            self.connector.set_public_permissions(new_doc_id)

            return new_doc_id
        except InvalidTemplateException as e:
            raise DocumentGenerationError(f"Template validation failed: {str(e)}")
        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate document: {str(e)}")