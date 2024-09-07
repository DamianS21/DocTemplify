# DocTemplify

DocTemplify is a Python library that streamlines document generation using Google Docs templates. It enables seamless creation of customized documents such as offers, invoices, and emails by leveraging existing Google Docs templates and filling them with dynamic data.

## Key Features

- Template-based document generation
- Google Docs integration
- Placeholder replacement with custom data
- Optional styling for placeholders
- Easy-to-use API for document creation and management (soon)
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

### Creating Document Templates and Populating with Data

DocTemplify makes it easy to create a document template and then generate documents using dynamic data. You can define the structure of the document in JSON, which includes placeholders for text, lists, tables, and images.

### Step 1: Define the Template Structure
The document template is defined in a JSON format, specifying different elements such as headings, paragraphs, lists, tables, and image placeholders.

```
template_structure = {
    "header": {
        "type": "heading",
        "content": "{{header}}",
        "level": 1,
        "style": {"color": "#000080"}
    },
    "introduction": {
        "type": "text",
        "content": "{{introduction}}",
        "style": {"font-style": "italic"}
    },
    "financial_summary": {
        "type": "heading",
        "content": "{{financial_summary}}",
        "level": 2
    },
    "key_metrics": {
        "type": "list",
        "items": [
            "{{key_metrics[0]}}",
            "{{key_metrics[1]}}",
            "{{key_metrics[2]}}"
        ]
    },
    "data_table": {
        "type": "table",
        "rows": 4,
        "cols": 2,
        "content": [
            ["{{data_table[0][0]}}", "{{data_table[0][1]}}"],
            ["{{data_table[1][0]}}", "{{data_table[1][1]}}"],
            ["{{data_table[2][0]}}", "{{data_table[2][1]}}"],
            ["{{data_table[3][0]}}", "{{data_table[3][1]}}"]
        ]
    },
    "company_logo": {
        "type": "image",
        "content": "{{IMAGE_PLACEHOLDER:company_logo}}",
        "style": {"width": "200px", "height": "100px"}
    },
    "conclusion": {
        "type": "text",
        "content": "{{conclusion}}"
    }
}
```

### Step 2: Create a Document Template
Once the template structure is defined, you can create the template document in Google Docs using the `TemplateCreator`.

```
from doctemplify import GoogleDocsConnector, TemplateCreator

# Initialize the Google Docs connector
connector = GoogleDocsConnector('path/to/your/service_account.json')

# Create the template creator
template_creator = TemplateCreator(connector)

# Create the document template
template_id, template_url = template_creator.create_template_from_json(
    template_structure,
    "Company Report Template",
    public=True
)

print(f"Template created with ID: {template_id}")
print(f"Template URL: {template_url}")

```

### Step 3: Define the Data for the Template
To generate a document based on the template, you need to provide a data dictionary. The keys should match the placeholders in your template.
```
document_data = {
    "header": "Company Report",
    "introduction": "This report provides an overview of our company's performance for Q3 2023.",
    "financial_summary": "Financial Summary",
    "key_metrics[0]": "Revenue: $500,000",
    "key_metrics[1]": "Expenses: $300,000",
    "key_metrics[2]": "Profit: $200,000",
    "data_table[0][0]": "Quarter",
    "data_table[0][1]": "Revenue",
    "data_table[1][0]": "Q1",
    "data_table[1][1]": "$400,000",
    "data_table[2][0]": "Q2",
    "data_table[2][1]": "$450,000",
    "data_table[3][0]": "Q3",
    "data_table[3][1]": "$500,000",
    "IMAGE_PLACEHOLDER:company_logo": {
        "url": "https://bioraslub.pl/wp-content/uploads/2022/10/biora-slub.png",
        "width": 200,
        "height": 100
    },
    "conclusion": "In conclusion, our company has shown strong growth this quarter, with revenue increasing by 11% compared to the previous quarter."
}
```

### Step 4: Generate a Document
Use the `DocumentGenerator` to populate the template with your data and create a new document.
```
from doctemplify import DocumentGenerator

# Create a document generator
document_generator = DocumentGenerator(connector)

# Generate the document
new_doc_id, new_doc_url = document_generator.generate_document(
    template_id,
    document_data,
    new_name='Q3 2023 Company Report',
    return_url=True
)

print(f"New document created with ID: {new_doc_id}")
print(f"New document URL: {new_doc_url}")
```

### Handling Image Placeholders
If your template contains image placeholders, such as `{{IMAGE_PLACEHOLDER:company_logo}}`, you can specify the image URL, width, and height in the data dictionary. The library will replace the placeholder with the image during document generation.


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
