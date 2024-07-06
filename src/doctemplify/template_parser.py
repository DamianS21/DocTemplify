import re
from typing import List, Dict, Any

class TemplateParser:
    def __init__(self, connector):
        self.connector = connector
        self.pattern = r'\{\{(.*?)\}\}'

    def find_parameters(self, text: str) -> List[str]:
        """
        Find all parameters in the given text, including optional style information.
        
        Args:
            text (str): The template text to parse.
        
        Returns:
            List[str]: A list of parameters, potentially including style information.
        """
        matches = re.findall(self.pattern, text)
        return list(set(match.strip() for match in matches))

    def validate_data(self, parameters: List[str], data: Dict[str, Any]) -> List[str]:
        """
        Validate that all parameters have corresponding data.
        
        Args:
            parameters (List[str]): List of parameters found in the template.
            data (Dict[str, Any]): The data dictionary to validate against.
        
        Returns:
            List[str]: A list of parameters that are missing from the data.
        """
        missing_params = []
        for param in parameters:
            # Extract the parameter name without any styling information
            param_name = param.split(':')[0].strip()
            if not self._check_nested_key(data, param_name):
                missing_params.append(param_name)
        return missing_params

    def _check_nested_key(self, data: Dict[str, Any], key: str) -> bool:
        """
        Check if a nested key exists in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The data dictionary to check.
            key (str): The key to check, can be dot-notated for nested structures.
        
        Returns:
            bool: True if the key exists, False otherwise.
        """
        keys = key.split('.')
        current = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        return True

    def _parse_css_style(self, style_string: str) -> Dict[str, str]:
        """
        Parse a CSS-like style string into a dictionary.

        Args:
            style_string (str): CSS-like style string.

        Returns:
            Dict[str, str]: Dictionary of style properties and values.
        """
        style_dict = {}
        styles = [s.strip() for s in style_string.split(';') if s.strip()]
        for style in styles:
            if ':' in style:
                key, value = style.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'font-family':
                    font = value.strip("'\"")
                    if font not in self.connector.GOOGLE_DOCS_FONTS:
                        print(f"Warning: Font '{font}' is not available in Google Docs. It will be ignored.")
                    else:
                        style_dict[key] = font
                else:
                    style_dict[key] = value

        return style_dict

class InvalidTemplateException(Exception):
    """Exception raised when the template is invalid."""
    pass