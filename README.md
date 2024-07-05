# DocTemplify

DocTemplify is a Python library that simplifies the process of generating documents using Google Docs templates. It allows you to create templates for various types of documents (such as offers, invoices, emails, etc.) in Google Docs, then use this library to fill in placeholders with actual data and create new documents based on those templates.

## Features

- Connect to Google Docs using a service account
- Copy template documents
- Replace placeholders in templates with actual data
- Set public permissions on generated documents
- Support for various document types (offers, invoices, emails, etc.)

## Installation

```
pip install doctemplify
```

## Usage

```python
from doctemplify import GoogleDocsConnector, DocumentGenerator

# Initialize the connector with your service account file
connector = GoogleDocsConnector('path/to/your/service_account.json')

# Create a document generator
generator = DocumentGenerator(connector)

# Generate a document
template_id = 'your_template_document_id'
data = {
    "client_name": "Acme Inc.",
    "offer": {
        "position": "Software Engineer",
        "salary": "$100,000"
    }
}

new_document_id = generator.generate_document(template_id, data, new_name='Client Offer')
print(f"New document created with ID: {new_document_id}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.