# DocTemplify

DocTemplify is a Python library that streamlines document generation using Google Docs templates. It enables seamless creation of customized documents such as offers, invoices, and emails by leveraging existing Google Docs templates and filling them with dynamic data.

Key features:
- Template-based document generation
- Google Docs integration
- Placeholder replacement with custom data
- Easy-to-use API for document creation and management

## Setup

### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the Google Drive API and Google Docs API for your project.

### 2. Create a Service Account
1. In your Google Cloud project, go to "IAM & Admin" > "Service Accounts".
2. Click "Create Service Account".
3. Enter a name for your service account (e.g., "doctemplify-service").
4. Grant this service account the "Editor" role for the project.
5. Create a JSON key for this service account and download it.

### 3. Share Your Template Document
1. Create your template document in Google Docs.
2. Click the "Share" button in the top right corner.
3. In the "Add people or groups" field, paste the email address of your service account. It should look similar to: 
   `your-service-account-name@your-project-id.iam.gserviceaccount.com`
4. Set the permission to "Editor".
5. Click "Send" to share the document with the service account.

### 4. Install DocTemplify
1. Clone the repository:
   ```
   git clone https://github.com/DamianS21/DocTemplify.git
   ```
2. Navigate to the DocTemplify directory:
   ```
   cd DocTemplify
   ```
3. Install the package in editable mode:
   ```
   pip install -e .
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