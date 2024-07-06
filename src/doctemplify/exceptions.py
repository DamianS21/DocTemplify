class GoogleAPIError(Exception):
    """Exception raised for errors in the Google API interactions."""
    pass

class DocumentGenerationError(Exception):
    """Exception raised for errors in document generation process."""
    pass

class TemplateParsingError(Exception):
    """Exception raised for errors in parsing the template document."""
    pass