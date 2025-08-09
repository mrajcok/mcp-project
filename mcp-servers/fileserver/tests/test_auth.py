# ABOUT-ME: Tests for bearer token authentication functionality using SQLite database
# ABOUT-ME: Verifies database-based token validation, user identification, and role assignment

import pytest
import os
from src.auth import verify_token
from src.db import init_user_db, add_test_user


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database for each test"""
    # pytest automatically sets PYTEST_CURRENT_TEST, so we don't need to manage it manually
    
    # Initialize test database
    init_user_db()
    
    # Add test users
    add_test_user('testuser', 'test-token-123')
    add_test_user('admin', 'admin-token-456')
    add_test_user('regularuser', 'user-token-789')
    
    yield


def test_valid_bearer_token():
    """Test that a valid bearer token is accepted and returns correct user info"""
    is_valid, username, role = verify_token('test-token-123')
    
    assert is_valid is True
    assert username == 'testuser'
    assert role == 'user'


def test_admin_bearer_token():
    """Test that admin token returns admin role"""
    is_valid, username, role = verify_token('admin-token-456')
    
    assert is_valid is True
    assert username == 'admin'
    assert role == 'admin'


def test_invalid_bearer_token():
    """Test that an invalid bearer token is rejected"""
    is_valid, username, role = verify_token('invalid-token')
    
    assert is_valid is False
    assert username is None
    assert role is None


def test_missing_bearer_token():
    """Test that missing token is handled properly"""
    is_valid, username, role = verify_token('')
    assert is_valid is False
    assert username is None
    assert role is None


def test_database_based_authentication():
    """Test that authentication uses database instead of environment variables"""
    # Regular user token
    is_valid, username, role = verify_token('user-token-789')
    assert is_valid is True
    assert username == 'regularuser'
    assert role == 'user'
    
    # Admin user (role determined by config admin_users list)
    is_valid, username, role = verify_token('admin-token-456') 
    assert is_valid is True
    assert username == 'admin'
    assert role == 'admin'


def test_role_from_config_not_database():
    """Test that user roles come from config admin_users list, not database"""
    # This verifies that role assignment is based on username in config.yaml admin_users
    is_valid, username, role = verify_token('admin-token-456')
    assert is_valid is True
    assert username == 'admin'
    assert role == 'admin'  # Because 'admin' is in config admin_users list
