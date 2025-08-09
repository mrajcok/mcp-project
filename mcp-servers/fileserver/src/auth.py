# ABOUT-ME: Authentication and authorization module for bearer token verification
# ABOUT-ME: Uses SQLite database for user/token verification with role determination from config

from typing import Tuple, Optional
from .db import verify_user_token


def verify_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify bearer token and return user information.
    
    Args:
        token: The bearer token to verify
        
    Returns:
        Tuple of (is_valid, username, role) where:
        - is_valid: True if token is valid, False otherwise
        - username: Username if valid, None if invalid
        - role: User role if valid, None if invalid
    """
    if not token:
        return False, None, None
    
    result = verify_user_token(token)
    if result:
        username, role = result
        return True, username, role
    
    return False, None, None
