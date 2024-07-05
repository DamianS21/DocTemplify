def extract_value_with_dot_notation(data, key):
    """Extract value from nested dictionary or list using dot notation."""
    keys = key.split('.')
    value = data
    try:
        for k in keys:
            if k.isdigit():
                value = value[int(k)]
            else:
                value = value[k]
    except (KeyError, TypeError, IndexError):
        value = 'Key not found'
    return value