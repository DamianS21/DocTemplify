from .exceptions import DocumentGenerationError

class DocumentGenerator:
    def __init__(self, google_docs_connector):
        self.connector = google_docs_connector

    def generate_document(self, template_id, data, new_name='Generated Document'):
        try:
            # Copy the template
            new_doc_id = self.connector.copy_template(template_id, new_name)

            # Replace placeholders with data
            self.connector.replace_placeholders(new_doc_id, data)

            # Set public permissions
            self.connector.set_public_permissions(new_doc_id)

            return new_doc_id
        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate document: {str(e)}")