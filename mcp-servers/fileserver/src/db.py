# ABOUT-ME: Database utilities for user authentication and token verification
# ABOUT-ME: Handles SQLite operations for user/token management with test database support

import sqlite3
import os
import logging
from typing import Optional, Tuple, List
from .utils import get_config

# Set up logging
logger = logging.getLogger(__name__)

# Load config once at module level
_CONFIG = get_config()


def get_user_db_path() -> str:
    """
    Get the path to the user database.
    
    Returns:
        Path to user database (test db if in test environment)
    """
    # Check if we're in a test environment
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return 'data/test_users.db'
    
    return _CONFIG['database']['user_db_path']


def init_user_db() -> None:
    """
    Initialize the user database with required tables.
    This is typically called by the external user management system,
    but we include it for testing purposes.
    """
    db_path = get_user_db_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize user database at {db_path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to create directory for database {db_path}: {e}")
        raise


def verify_user_token(token: str) -> Optional[Tuple[str, str]]:
    """
    Verify bearer token against user database and return user info.
    
    Args:
        token: Bearer token to verify
        
    Returns:
        Tuple of (username, role) if token is valid, None otherwise
    """
    if not token:
        return None
    
    db_path = get_user_db_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM users WHERE token = ?', (token,))
            result = cursor.fetchone()
            
            if result:
                username = result[0]
                # Determine role from config admin_users list
                admin_users = _CONFIG.get('admin_users', [])
                role = 'admin' if username in admin_users else 'user'
                return username, role
                
    except sqlite3.Error as e:
        logger.error(f"Database error during token verification for token {token[:8]}...: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None
    
    return None


def add_test_user(username: str, token: str) -> bool:
    """
    Add a test user to the database. Only works in test environment.
    
    Args:
        username: Username to add
        token: Bearer token for the user
        
    Returns:
        True if user was added, False otherwise
    """
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        return False
    
    db_path = get_user_db_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute('INSERT OR REPLACE INTO users (username, token) VALUES (?, ?)', 
                        (username, token))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to add test user {username}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding test user {username}: {e}")
        return False


def get_usage_db_path() -> str:
    """
    Get the path to the usage database.
    
    Returns:
        Path to usage database (test db if in test environment)
    """
    # Check if we're in a test environment
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return 'data/test_usage.db'
    
    return _CONFIG.get('database', {}).get('usage_db_path', 'data/usage.db')


def init_usage_db(db_path: Optional[str] = None) -> None:
    """
    Initialize the usage database with required tables.
    
    Args:
        db_path: Optional path to database (uses default if not provided)
    """
    if db_path is None:
        db_path = get_usage_db_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage (
                    username TEXT NOT NULL,
                    date TEXT NOT NULL,
                    request_count INTEGER DEFAULT 0,
                    PRIMARY KEY (username, date)
                )
            ''')
            conn.commit()
            
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize usage database at {db_path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to create directory for database {db_path}: {e}")
        raise


def increment_usage(username: str, db_path: Optional[str] = None) -> None:
    """
    Increment daily usage counter for a user.
    
    Args:
        username: Username to increment usage for
        db_path: Optional path to database (uses default if not provided)
    """
    if db_path is None:
        db_path = get_usage_db_path()
    
    # Get current date
    from datetime import date
    today = date.today().isoformat()
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Use INSERT OR REPLACE to handle both new entries and updates
            conn.execute('''
                INSERT INTO usage (username, date, request_count)
                VALUES (?, ?, 1)
                ON CONFLICT(username, date) 
                DO UPDATE SET request_count = request_count + 1
            ''', (username, today))
            conn.commit()
            
    except sqlite3.Error as e:
        logger.error(f"Failed to increment usage for user {username}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error incrementing usage for user {username}: {e}")
        raise


def check_rate_limit(username: str, db_path: Optional[str] = None) -> Tuple[bool, int]:
    """
    Check if a user has exceeded their daily rate limit.
    
    Args:
        username: Username to check rate limit for
        db_path: Optional path to database (uses default if not provided)
        
    Returns:
        Tuple of (is_within_limit, current_usage_count)
        is_within_limit is False if user has exceeded the daily limit
    """
    if db_path is None:
        db_path = get_usage_db_path()
    
    # Get current date and rate limit from config
    from datetime import date
    today = date.today().isoformat()
    daily_limit = _CONFIG.get('rate_limit', {}).get('daily_requests', 1000)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT request_count FROM usage 
                WHERE username = ? AND date = ?
            ''', (username, today))
            result = cursor.fetchone()
            
            current_usage = result[0] if result else 0
            is_within_limit = current_usage < daily_limit
            
            return is_within_limit, current_usage
            
    except sqlite3.Error as e:
        logger.error(f"Failed to check rate limit for user {username}: {e}")
        # In case of database error, allow the request (fail open)
        return True, 0
    except Exception as e:
        logger.error(f"Unexpected error checking rate limit for user {username}: {e}")
        # In case of unexpected error, allow the request (fail open)
        return True, 0


def is_system_degraded(db_path: Optional[str] = None) -> bool:
    """
    Check if the system is in degraded state due to any user exceeding limits.
    
    Args:
        db_path: Optional path to database (uses default if not provided)
        
    Returns:
        True if system should be in degraded state, False otherwise
    """
    if db_path is None:
        db_path = get_usage_db_path()
    
    # Get current date and rate limit from config
    from datetime import date
    today = date.today().isoformat()
    daily_limit = _CONFIG.get('rate_limit', {}).get('daily_requests', 1000)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM usage 
                WHERE date = ? AND request_count > ?
            ''', (today, daily_limit))
            result = cursor.fetchone()
            
            # If any user has exceeded the limit today, system is degraded
            users_over_limit = result[0] if result else 0
            return users_over_limit > 0
            
    except sqlite3.Error as e:
        logger.error(f"Failed to check system degraded state: {e}")
        # In case of database error, assume not degraded (fail open)
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking system degraded state: {e}")
        # In case of unexpected error, assume not degraded (fail open)
        return False


def get_degraded_users(db_path: Optional[str] = None) -> List[str]:
    """
    Get list of users who have exceeded their daily rate limit.
    
    Args:
        db_path: Optional path to database (uses default if not provided)
        
    Returns:
        List of usernames who have exceeded their daily limit
    """
    if db_path is None:
        db_path = get_usage_db_path()
    
    # Get current date and rate limit from config
    from datetime import date
    today = date.today().isoformat()
    daily_limit = _CONFIG.get('rate_limit', {}).get('daily_requests', 1000)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username FROM usage 
                WHERE date = ? AND request_count > ?
            ''', (today, daily_limit))
            results = cursor.fetchall()
            
            return [row[0] for row in results]
            
    except sqlite3.Error as e:
        logger.error(f"Failed to get degraded users: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting degraded users: {e}")
        return []
