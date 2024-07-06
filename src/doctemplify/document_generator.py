from typing import Dict, Any, Union, Tuple
from .exceptions import DocumentGenerationError
from .google_docs_connector import GoogleDocsConnector, GDOCS_DEFAULT_URL

class DocumentGenerator:
    def __init__(self, google_docs_connector: GoogleDocsConnector):
        self.connector = google_docs_connector

    def generate_document(self, template_id: str, data: Dict[str, Any], new_name: str = 'Generated Document', return_url: bool = False) -> Union[str, Tuple[str, str]]:
        """
        Generate a new document based on a template and provided data.

        Args:
            template_id (str): The ID of the template document.
            data (Dict[str, Any]): The data to populate the template with.
            new_name (str, optional): The name for the new document. Defaults to 'Generated Document'.
            return_url (bool, optional): Whether to return the document URL along with the ID. Defaults to False.

        Returns:
            Union[str, Tuple[str, str]]: If return_url is False, returns the new document ID.
                                         If return_url is True, returns a tuple of (document_id, document_url).

        Raises:
            DocumentGenerationError: If there's an error during document generation.
        """
        try:
            # Validate the template before copying
            self.connector.validate_template(template_id, data)

            # Copy the template
            new_doc_id = self.connector.copy_template(template_id, new_name)

            # Replace placeholders with data
            self.connector.replace_placeholders(new_doc_id, data)

            # Set public permissions
            self.connector.set_public_permissions(new_doc_id)

            if return_url:
                doc_url = GDOCS_DEFAULT_URL.format(new_doc_id)
                return new_doc_id, doc_url
            else:
                return new_doc_id

        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate document: {str(e)}")