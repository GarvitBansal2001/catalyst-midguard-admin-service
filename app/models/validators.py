def validate_permission_set(permissions: dict, **kwargs) -> dict:
    """
    Validates a permission set dictionary ensuring:
    - Input can be None or dict
    - Only read/write keys are allowed
    - Values must be 1 or None
    Returns validated dictionary with non-None values
    """
    # Handle None input
    if permissions is None:
        return {}
        
    # Validate input type
    if not isinstance(permissions, dict):
        raise ValueError("Permissions must be a dictionary")
        
    # Create new dict only with non-None values that are 1
    cleaned_permissions = {}
    for key, value in permissions.items():
        if key not in ["read", "write"]:
            raise ValueError(f"Invalid permission key: {key}")
        if value not in [1, None]:
            raise ValueError(f"Permission value for {key} must be exactly 1, got {value}")
        if value is not None:
            cleaned_permissions[key] = value
    return cleaned_permissions