"""
Response Utilities for API Security

This module provides sanitization utilities to ensure sensitive fields
like passwords are never exposed in API responses.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Sensitive field names that should never be exposed in API responses
SENSITIVE_FIELDS = [
    'password',
    'password_hash', 
    'senha',
    'senha_hash',
    'senha_admin',
    'senha_temporaria',
    'secret',
    'secret_key',
    'api_key',
    'token',
    'access_token',
    'refresh_token',
]


def sanitize_response(data: Any, additional_fields: Optional[List[str]] = None) -> Any:
    """
    Remove sensitive fields from response data.
    
    This function recursively processes dictionaries and lists to ensure
    no password or other sensitive fields are exposed in API responses.
    
    Args:
        data: The data to sanitize (dict, list, or any other type)
        additional_fields: Optional list of additional field names to filter
        
    Returns:
        Sanitized data with sensitive fields removed
        
    Example:
        >>> sanitize_response({'id': 1, 'username': 'admin', 'senha': 'secret'})
        {'id': 1, 'username': 'admin'}
    """
    if data is None:
        return None
        
    sensitive = SENSITIVE_FIELDS.copy()
    if additional_fields:
        sensitive.extend(additional_fields)
    
    if isinstance(data, dict):
        return {
            k: sanitize_response(v, additional_fields)
            for k, v in data.items()
            if k not in sensitive
        }
    
    if isinstance(data, list):
        return [sanitize_response(item, additional_fields) for item in data]
    
    # For any other type, return as-is
    return data


def sanitize_estabelecimento(data: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Sanitize establishment data specifically.
    
    Ensures password fields are never included in establishment responses.
    
    Args:
        data: Establishment data (dict or model instance)
        
    Returns:
        Sanitized dictionary
    """
    if data is None:
        return None
        
    if hasattr(data, 'to_dict'):
        data = data.to_dict()
    
    return sanitize_response(data)


def sanitize_funcionario(data: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Sanitize employee/user data specifically.
    
    Ensures password fields (senha, password_hash) are never included in user responses.
    
    Args:
        data: Funcionario data (dict or model instance)
        
    Returns:
        Sanitized dictionary
    """
    if data is None:
        return None
        
    if hasattr(data, 'to_dict'):
        data = data.to_dict()
    
    return sanitize_response(data)


def sanitize_user(data: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Alias for sanitize_funcionario for clarity.
    
    Args:
        data: User data (dict or model instance)
        
    Returns:
        Sanitized dictionary
    """
    return sanitize_funcionario(data)


def create_safe_response(success: bool, data: Any = None, message: str = None, **kwargs) -> Dict:
    """
    Create a sanitized response dictionary.
    
    Convenience function that combines response creation with sanitization.
    
    Args:
        success: Whether the operation was successful
        data: The data to include (will be sanitized)
        message: Optional message
        **kwargs: Additional fields to include in response
        
    Returns:
        Sanitized response dictionary
    """
    response = {'success': success}
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = sanitize_response(data)
    
    response.update(sanitize_response(kwargs))
    
    return response
