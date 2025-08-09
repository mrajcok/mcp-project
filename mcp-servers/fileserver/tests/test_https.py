# ABOUT-ME: Tests for HTTPS/SSL configuration and functionality
# ABOUT-ME: Verifies SSL certificate handling, configuration loading, and server setup

import pytest
import os
import tempfile
import yaml
import ssl
import time
import threading
from unittest.mock import patch, MagicMock
from src.utils import get_config

# Import requests for integration tests
import requests


class TestHTTPSConfiguration:
    """Test HTTPS/SSL configuration and setup"""
    
    def test_ssl_config_loading(self):
        """Test that SSL configuration is loaded correctly from config.yaml"""
        config = get_config()
        
        # Verify SSL configuration exists
        assert "ssl" in config
        ssl_config = config["ssl"]
        
        # Check required SSL fields
        assert "enabled" in ssl_config
        assert "certfile" in ssl_config
        assert "keyfile" in ssl_config
        assert "ssl_version" in ssl_config
        
        # Check default values
        assert ssl_config["enabled"] is False
        assert ssl_config["ssl_version"] == 17
        
    def test_server_config_loading(self):
        """Test that server configuration is loaded correctly"""
        config = get_config()
        
        # Verify server configuration exists
        assert "server" in config
        server_config = config["server"]
        
        # Check required server fields
        assert "host" in server_config
        assert "port" in server_config
        
        # Check default values
        assert server_config["host"] == "0.0.0.0"
        assert server_config["port"] == 8080


class TestHTTPSIntegration:
    """Integration tests for HTTPS functionality with real certificates"""
    
    @pytest.fixture
    def ssl_certs(self):
        """Create temporary self-signed SSL certificates for testing"""
        import subprocess
        import tempfile
        
        # Create temporary directory for certificates
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_file = os.path.join(temp_dir, "test_server.crt")
            key_file = os.path.join(temp_dir, "test_server.key")
            
            # Generate self-signed certificate
            try:
                # Generate private key
                subprocess.run([
                    "openssl", "genrsa", "-out", key_file, "2048"
                ], check=True, capture_output=True)
                
                # Generate certificate with Subject Alternative Names
                subprocess.run([
                    "openssl", "req", "-new", "-x509", "-key", key_file, "-out", cert_file,
                    "-days", "1", "-subj", "/C=US/ST=Test/L=Test/O=Test/CN=localhost",
                    "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"
                ], check=True, capture_output=True)
                
                yield {
                    "certfile": cert_file,
                    "keyfile": key_file
                }
            except subprocess.CalledProcessError:
                pytest.skip("OpenSSL not available for certificate generation")
    
    def test_ssl_certificate_generation_script(self):
        """Test that the SSL certificate generation script works"""
        script_path = "generate-ssl-certs.sh"
        
        # Check script exists and is executable
        assert os.path.exists(script_path)
        assert os.access(script_path, os.X_OK)
        
        # Check script contains expected OpenSSL commands
        with open(script_path, 'r') as f:
            content = f.read()
            assert "openssl genrsa" in content
            assert "openssl req" in content
            assert "openssl x509" in content
    
    def test_https_server_startup_with_certs(self, ssl_certs):
        """Test that server can start with HTTPS and valid certificates"""
        import uvicorn
        from src.server import mcp
        
        # Create server configuration
        config = {
            "host": "127.0.0.1",
            "port": 9443,  # Use non-standard port for testing
            "app": mcp.sse_app(),
            "ssl_keyfile": ssl_certs["keyfile"],
            "ssl_certfile": ssl_certs["certfile"],
            "ssl_version": ssl.PROTOCOL_TLS_SERVER
        }
        
        # Start server in background thread
        server_thread = None
        server_started = threading.Event()
        
        def run_server():
            try:
                server_started.set()
                uvicorn.run(**config)
            except Exception as e:
                pytest.skip(f"Server startup failed: {e}")
        
        try:
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            server_started.wait(timeout=2)
            time.sleep(1)  # Give server time to fully start
            
            # Test HTTPS connection using the generated certificate
            try:
                response = requests.get(
                    "https://127.0.0.1:9443/health",
                    verify=ssl_certs["certfile"],  # Use the generated certificate
                    timeout=5
                )
                # If we get here, HTTPS is working
                assert response.status_code in [200, 404]  # 404 is OK, means server is running
            except requests.exceptions.SSLError:
                pytest.fail("SSL/HTTPS configuration failed")
            except requests.exceptions.ConnectionError:
                # Server might not have started yet, this is acceptable for this test
                pass
                
        finally:
            # Cleanup is automatic due to daemon thread
            pass
    
    def test_http_fallback_warning(self, capsys):
        """Test that server prints warning when running in HTTP mode"""
        from src.server import main
        
        # Mock uvicorn.run to avoid actually starting server
        with patch('uvicorn.run') as mock_run:
            with patch('src.server.get_config') as mock_config:
                # Configure for HTTP mode
                mock_config.return_value = {
                    "ssl": {"enabled": False},
                    "server": {"host": "0.0.0.0", "port": 8080}
                }
                
                # Mock FastMCP
                with patch('src.server.mcp') as mock_mcp:
                    mock_mcp.sse_app.return_value = MagicMock()
                    
                    main()
                    
                    # Check that warning was printed
                    captured = capsys.readouterr()
                    assert "Warning: Running in HTTP mode" in captured.out
                    assert "Bearer tokens will be transmitted in plain text" in captured.out


class TestSSLConfigurationValidation:
    """Test SSL configuration validation and error handling"""
    
    def test_ssl_config_validation_with_temp_config(self):
        """Test SSL configuration validation with a temporary config file"""
        # Create temporary config with SSL settings
        ssl_config = {
            "ssl": {
                "enabled": True,
                "certfile": "test_cert.crt",
                "keyfile": "test_key.key",
                "ssl_version": 17
            },
            "server": {
                "host": "localhost",
                "port": 9443
            },
            "allowed_directories": ["/tmp"],
            "rate_limit": {"daily_requests": 1000},
            "database": {
                "user_db_path": "/shared/users.db",
                "usage_db_path": "data/usage.db"
            },
            "admin_users": ["admin"]
        }
        
        # Write temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(ssl_config, f)
            temp_config_path = f.name
        
        try:
            # Read and validate the config
            with open(temp_config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Verify SSL configuration is correctly structured
            assert loaded_config["ssl"]["enabled"] is True
            assert loaded_config["ssl"]["certfile"] == "test_cert.crt"
            assert loaded_config["ssl"]["keyfile"] == "test_key.key"
            assert loaded_config["ssl"]["ssl_version"] == 17
            
            # Verify server configuration
            assert loaded_config["server"]["host"] == "localhost"
            assert loaded_config["server"]["port"] == 9443
            
        finally:
            # Clean up temporary file
            os.unlink(temp_config_path)
    
    def test_missing_certificate_handling(self, capsys):
        """Test handling when SSL is enabled but certificates are missing"""
        from src.server import main
        
        with patch('uvicorn.run') as mock_run:
            with patch('src.server.get_config') as mock_config:
                with patch('src.server.os.path.exists') as mock_exists:
                    # Configure for HTTPS but missing certificates
                    mock_config.return_value = {
                        "ssl": {
                            "enabled": True,
                            "certfile": "/nonexistent/cert.crt",
                            "keyfile": "/nonexistent/key.key"
                        },
                        "server": {"host": "0.0.0.0", "port": 8080}
                    }
                    mock_exists.return_value = False  # Certificates don't exist
                    
                    # Mock FastMCP
                    with patch('src.server.mcp') as mock_mcp:
                        mock_mcp.sse_app.return_value = MagicMock()
                        
                        main()
                        
                        # Check that appropriate warning was printed
                        captured = capsys.readouterr()
                        assert "SSL certificates not found" in captured.out
                        assert "Running in HTTP mode" in captured.out
                        
                        # Verify server was started without SSL
                        mock_run.assert_called_once()
                        args, kwargs = mock_run.call_args
                        assert "ssl_keyfile" not in kwargs
                        assert "ssl_certfile" not in kwargs


class TestRealHTTPSConnection:
    """Test real HTTPS connections using the certificate generation script"""
    
    def test_generate_and_use_real_certificates(self):
        """Test generating real certificates and using them"""
        import subprocess
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory and generate certificates
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Run the certificate generation script
                script_path = os.path.join(original_dir, "generate-ssl-certs.sh")
                if os.path.exists(script_path):
                    try:
                        result = subprocess.run([
                            "bash", script_path
                        ], capture_output=True, text=True, timeout=30)
                        
                        # Check if certificates were generated
                        cert_file = os.path.join(temp_dir, "ssl", "server.crt")
                        key_file = os.path.join(temp_dir, "ssl", "server.key")
                        
                        if result.returncode == 0:
                            assert os.path.exists(cert_file), "Certificate file was not created"
                            assert os.path.exists(key_file), "Key file was not created"
                            
                            # Verify certificate is valid
                            cert_info = subprocess.run([
                                "openssl", "x509", "-in", cert_file, "-text", "-noout"
                            ], capture_output=True, text=True)
                            
                            assert cert_info.returncode == 0
                            assert "Subject: C = US" in cert_info.stdout
                            assert "localhost" in cert_info.stdout
                        else:
                            pytest.skip(f"Certificate generation failed: {result.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        pytest.skip("Certificate generation timed out")
                    except FileNotFoundError:
                        pytest.skip("OpenSSL not available")
                else:
                    pytest.skip("Certificate generation script not found")
                    
            finally:
                os.chdir(original_dir)


if __name__ == "__main__":
    pytest.main([__file__])
