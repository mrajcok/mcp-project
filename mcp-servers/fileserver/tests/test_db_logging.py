# ABOUT-ME: Test for database error logging functionality
# ABOUT-ME: Verifies that database errors are properly logged with appropriate detail

import pytest
import os
import logging
import tempfile
from unittest.mock import patch, MagicMock
from src.db import verify_user_token, init_user_db, add_test_user


def test_database_error_logging(caplog):
    """Test that database errors are properly logged"""
    
    # pytest automatically sets PYTEST_CURRENT_TEST, so we don't need to manage it manually
    
    # Mock sqlite3.connect to raise an error
    with patch('src.db.sqlite3.connect') as mock_connect:
        mock_connect.side_effect = Exception("Database connection failed")
        
        # Set logging level to capture error logs
        with caplog.at_level(logging.ERROR):
            result = verify_user_token('test-token')
            
        # Verify the function handled the error gracefully
        assert result is None
        
        # Verify error was logged
        assert len(caplog.records) > 0
        assert "Unexpected error during token verification" in caplog.text
        assert "Database connection failed" in caplog.text


def test_database_init_error_logging(caplog):
    """Test that database initialization errors are properly logged"""
    
    # pytest automatically sets PYTEST_CURRENT_TEST, so we don't need to manage it manually
    
    # Mock os.makedirs to raise an error
    with patch('src.db.os.makedirs') as mock_makedirs:
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # Set logging level to capture error logs
        with caplog.at_level(logging.ERROR):
            with pytest.raises(OSError):
                init_user_db()
                
        # Verify error was logged
        assert len(caplog.records) > 0
        assert "Failed to create directory for database" in caplog.text
        assert "Permission denied" in caplog.text
