import logging
import re
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def get_nested_value(
    data: Dict[str, Any], 
    path: str, 
    default: Any = None
) -> Any:
    """
    Get a value from a nested dictionary using a path string.
    
    Args:
        data: Dictionary to extract value from
        path: Path string (e.g., "params[0]", "pool.name")
        default: Default value if path not found
        
    Returns:
        Extracted value or default if not found
    """
    try:
        # Handle array indices
        array_match = re.match(r"([a-zA-Z0-9_.]+)\[(\d+)\]", path)
        if array_match:
            base_path, index = array_match.groups()
            index = int(index)
            
            # Get base value
            base_value = get_nested_value(data, base_path)
            
            # Check if it's a list and index is valid
            if isinstance(base_value, list) and 0 <= index < len(base_value):
                return base_value[index]
            else:
                return default
        
        # Handle dot notation
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
        
    except Exception as e:
        logger.debug(f"Error getting nested value for path '{path}': {e}")
        return default

def safe_concat(*args: Any) -> str:
    """
    Safely concatenate any number of values as strings.
    
    Args:
        *args: Values to concatenate
        
    Returns:
        Concatenated string
    """
    result = ""
    for arg in args:
        if arg is not None:
            result += str(arg)
    return result

def safe_get(
    data: Dict[str, Any], 
    key: str, 
    default: Any = None
) -> Any:
    """
    Safely get a value from a dictionary.
    
    Args:
        data: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found or data is not a dict
        
    Returns:
        Value or default
    """
    if not isinstance(data, dict):
        return default
    return data.get(key, default)

def extract_array_value(
    arr: List[Any], 
    index: int, 
    default: Any = None
) -> Any:
    """
    Safely extract a value from an array by index.
    
    Args:
        arr: Array to extract from
        index: Index to extract
        default: Default value if index is invalid
        
    Returns:
        Value at index or default
    """
    if not isinstance(arr, list) or index < 0 or index >= len(arr):
        return default
    return arr[index]

def convert_type(
    value: Any,
    target_type: str,
    default: Any = None
) -> Any:
    """
    Convert a value to a specified type.
    
    Args:
        value: Value to convert
        target_type: Target type ('str', 'int', 'float', 'bool', 'list', 'dict')
        default: Default value if conversion fails
        
    Returns:
        Converted value or default
    """
    try:
        if target_type == 'str':
            return str(value)
        elif target_type == 'int':
            return int(float(value))
        elif target_type == 'float':
            return float(value)
        elif target_type == 'bool':
            if isinstance(value, bool):
                return value
            elif isinstance(value, (int, float)):
                return bool(value)
            elif isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 't', 'y')
            else:
                return default
        elif target_type == 'list':
            if isinstance(value, list):
                return value
            elif value is None:
                return []
            else:
                return [value]
        elif target_type == 'dict':
            if isinstance(value, dict):
                return value
            else:
                return default
        else:
            return default
    except Exception:
        return default