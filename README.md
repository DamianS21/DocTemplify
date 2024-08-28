# DocTemplify

DocTemplify is a Python library that streamlines document generation using Google Docs templates. It enables seamless creation of customized documents such as offers, invoices, and emails by leveraging existing Google Docs templates and filling them with dynamic data.

## Key Features

- Template-based document generation
- Google Docs integration
- Placeholder replacement with custom data
- Optional styling for placeholders
- Easy-to-use API for document creation and management
- Automatic generation of document URLs

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

### Creating Template Variables

DocTemplify supports two types of variables in your Google Docs templates:

1. **Simple Variables**: These are replaced with plain text.
2. **Styled Variables**: These are replaced with text that has specific styling applied.

#### Simple Variables

To create a simple variable, use double curly braces:

```
{{variable_name}}
```

Example:
```
Dear {{client_name}},

Thank you for your interest in our {{product_name}}.
```

#### Styled Variables

To create a styled variable, use double curly braces with a colon followed by CSS-like styling:

```
{{variable_name : style1: value1; style2: value2;}}
```

Example:
```
{{company_name.main : color: #333333; font-weight: bold; font-size: 18pt; font-family: "Arial"}}
{{company_name.accent : color: #0066cc; font-style: italic; font-size: 16px; font-family: "Georgia"}}
```

### Styling in DocTemplify

DocTemplify supports styled variables, but it's important to understand how the styling is applied:

1. Styles for variables are specified in the data provided when generating the document.
2. Any styling specified in the document template placeholders is not applied to the final document.

#### Supported Style Properties

When providing styles in the data, you can use the following properties:

- `color`: Text color (e.g., `#FF0000`, `rgb(255, 0, 0)`, or color names)
- `background-color`: Background color
- `font-weight`: `normal` or `bold`
- `font-style`: `normal` or `italic`
- `font-size`: Size in `pt` or `px`
- `font-family`: Font name (must be available in Google Docs)
- `text-decoration`: `underline` or `line-through`

### Providing Data

When using DocTemplify, you need to provide a dictionary that matches the variables in your template. For simple variables, use string values. For styled variables, provide a dictionary with 'value' and 'style' keys.

Example:

```python
data = {
    "client_name": "John Doe",
    "product_name": "Solar Panel System",
    "company_name": {
        "main": {
            "value": "SOLAR",
            "style": "color: #333333; font-weight: bold; font-size: 18pt; font-family: 'Arial'"
        },
        "accent": {
            "value": "TECH",
            "style": "color: #0066cc; font-style: italic; font-size: 16px; font-family: 'Georgia'"
        }
    },
    "offer_details": {
        "system_size": "5 kW",
        "panel_count": 15,
        "estimated_savings": "$1,200 per year"
    },
    "footer_text": {
        "value": "Thank you for choosing our services!",
        "style": "font-size: 10pt; font-style: italic;"
    }
}
```

### Generating Documents

```python
from doctemplify import GoogleDocsConnector, DocumentGenerator

# Initialize the connector with your service account file
connector = GoogleDocsConnector('path/to/your/service_account.json')

# Create a document generator
generator = DocumentGenerator(connector)

# Generate a document
template_id = 'your_template_document_id'
data = {
    "client_name": "John Doe",
    "product_name": "Solar Panel System",
    # ... other data ...
}

# Generate document and get both ID and URL
new_document_id, new_document_url = generator.generate_document(
    template_id, 
    data, 
    new_name='Client Offer',
    return_url=True
)

print(f"New document created:")
print(f"ID: {new_document_id}")
print(f"URL: {new_document_url}")
```

The `generate_document` method now returns both the document ID and URL when `return_url=True` is specified.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
