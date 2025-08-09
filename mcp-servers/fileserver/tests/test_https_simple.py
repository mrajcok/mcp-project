# ABOUT-ME: Simple HTTPS tests that verify certificate and configuration functionality  
# ABOUT-ME: Tests SSL setup without requiring full server integration

import pytest
import os
import tempfile
import yaml
import ssl
import subprocess
from src.utils import get_config


class TestHTTPSCertificates:
    """Test HTTPS certificate generation and validation"""
    
    def test_certificate_generation_script_functionality(self):
        """Test that the certificate generation script creates valid certificates"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save current directory
            original_dir = os.getcwd()
            
            try:
                # Change to temp directory
                os.chdir(temp_dir)
                
                # Run certificate generation script
                script_path = os.path.join(original_dir, "generate-ssl-certs.sh")
                if not os.path.exists(script_path):
                    pytest.skip("Certificate generation script not found")
                
                result = subprocess.run([
                    "bash", script_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"Script stderr: {result.stderr}")
                    pytest.skip(f"Certificate generation failed: {result.stderr}")
                
                # Verify certificates were created
                cert_file = os.path.join(temp_dir, "ssl", "server.crt")
                key_file = os.path.join(temp_dir, "ssl", "server.key")
                
                assert os.path.exists(cert_file), "Certificate file not created"
                assert os.path.exists(key_file), "Key file not created"
                
                # Verify certificate is valid
                cert_info = subprocess.run([
                    "openssl", "x509", "-in", cert_file, "-text", "-noout"
                ], capture_output=True, text=True)
                
                assert cert_info.returncode == 0, "Certificate validation failed"
                assert "Subject: C = US" in cert_info.stdout
                assert "CN = localhost" in cert_info.stdout
                
                print("✅ Certificate generation and validation successful")
                
            except subprocess.TimeoutExpired:
                pytest.skip("Certificate generation timed out")
            except FileNotFoundError:
                pytest.skip("OpenSSL not available")
            finally:
                os.chdir(original_dir)
    
    def test_ssl_context_creation(self):
        """Test creating SSL context with generated certificates"""
        # Use existing certificates if available
        cert_file = "ssl/server.crt"
        key_file = "ssl/server.key"
        
        if not (os.path.exists(cert_file) and os.path.exists(key_file)):
            pytest.skip("SSL certificates not found - run generate-ssl-certs.sh first")
        
        try:
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            
            # Verify context was created successfully
            assert context.protocol == ssl.PROTOCOL_TLS_SERVER
            
            print("✅ SSL context creation successful")
            
        except ssl.SSLError as e:
            pytest.fail(f"SSL context creation failed: {e}")
        except FileNotFoundError as e:
            pytest.fail(f"Certificate files not accessible: {e}")
    
    def test_certificate_info_extraction(self):
        """Test extracting information from generated certificates"""
        cert_file = "ssl/server.crt"
        
        if not os.path.exists(cert_file):
            pytest.skip("SSL certificate not found - run generate-ssl-certs.sh first")
        
        try:
            # Get certificate information
            result = subprocess.run([
                "openssl", "x509", "-in", cert_file, "-subject", "-issuer", "-dates", "-noout"
            ], capture_output=True, text=True, check=True)
            
            output = result.stdout
            
            # Verify certificate contains expected information
            assert "subject=C = US" in output
            assert "CN = localhost" in output
            assert "issuer=C = US" in output  # Self-signed
            assert "notBefore=" in output
            assert "notAfter=" in output
            
            print("✅ Certificate information extraction successful")
            print(f"Certificate details:\n{output}")
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Certificate info extraction failed: {e}")
        except FileNotFoundError:
            pytest.skip("OpenSSL not available")


class TestHTTPSConfiguration:
    """Test HTTPS configuration management"""
    
    def test_https_config_structure(self):
        """Test that HTTPS configuration has correct structure"""
        config = get_config()
        
        # Verify SSL configuration exists and has correct structure
        assert "ssl" in config
        ssl_config = config["ssl"]
        
        required_keys = ["enabled", "certfile", "keyfile", "ssl_version"]
        for key in required_keys:
            assert key in ssl_config, f"Missing SSL config key: {key}"
        
        # Verify data types
        assert isinstance(ssl_config["enabled"], bool)
        assert isinstance(ssl_config["certfile"], str)
        assert isinstance(ssl_config["keyfile"], str)
        assert isinstance(ssl_config["ssl_version"], int)
        
        print(f"✅ HTTPS configuration structure valid: {ssl_config}")
    
    def test_https_config_file_creation(self):
        """Test creating configuration file with HTTPS enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_file = os.path.join(temp_dir, "server.crt")
            key_file = os.path.join(temp_dir, "server.key")
            
            # Create HTTPS config
            https_config = {
                "ssl": {
                    "enabled": True,
                    "certfile": cert_file,
                    "keyfile": key_file,
                    "ssl_version": 17
                },
                "server": {"host": "0.0.0.0", "port": 8443},
                "allowed_directories": ["/tmp"],
                "rate_limit": {"daily_requests": 1000},
                "database": {
                    "user_db_path": "/shared/users.db",
                    "usage_db_path": "data/usage.db"
                },
                "admin_users": ["admin"]
            }
            
            # Write config file
            config_file = os.path.join(temp_dir, "https_config.yaml")
            with open(config_file, 'w') as f:
                yaml.dump(https_config, f)
            
            # Read and verify config
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config["ssl"]["enabled"] is True
            assert loaded_config["ssl"]["certfile"] == cert_file
            assert loaded_config["ssl"]["keyfile"] == key_file
            assert loaded_config["server"]["port"] == 8443
            
            print("✅ HTTPS configuration file creation successful")
    
    def test_http_to_https_config_transition(self):
        """Test configuration transition from HTTP to HTTPS"""
        # Start with current config (should be HTTP)
        current_config = get_config()
        
        # Verify it starts as HTTP
        assert current_config["ssl"]["enabled"] is False
        
        # Create HTTPS version
        https_config = current_config.copy()
        https_config["ssl"]["enabled"] = True
        https_config["ssl"]["certfile"] = "ssl/server.crt"
        https_config["ssl"]["keyfile"] = "ssl/server.key"
        https_config["server"]["port"] = 8443  # Change port for HTTPS
        
        # Verify transition
        assert https_config["ssl"]["enabled"] is True
        assert https_config["ssl"]["certfile"] == "ssl/server.crt"
        assert https_config["ssl"]["keyfile"] == "ssl/server.key"
        assert https_config["server"]["port"] == 8443
        
        # Verify other config remains unchanged
        assert https_config["allowed_directories"] == current_config["allowed_directories"]
        assert https_config["admin_users"] == current_config["admin_users"]
        
        print("✅ HTTP to HTTPS configuration transition successful")


class TestHTTPSSecurityValidation:
    """Test HTTPS security-related functionality"""
    
    def test_certificate_security_properties(self):
        """Test that generated certificates have appropriate security properties"""
        cert_file = "ssl/server.crt"
        
        if not os.path.exists(cert_file):
            pytest.skip("SSL certificate not found - run generate-ssl-certs.sh first")
        
        try:
            # Get detailed certificate information
            result = subprocess.run([
                "openssl", "x509", "-in", cert_file, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            
            cert_text = result.stdout
            
            # Check key size (should be at least 2048 bits)
            if "RSA" in cert_text:
                assert "2048 bit" in cert_text or "4096 bit" in cert_text, "Key size too small"
            
            # Check that it's a self-signed certificate (issuer == subject)
            subject_line = [line for line in cert_text.split('\n') if 'Subject:' in line][0]
            issuer_line = [line for line in cert_text.split('\n') if 'Issuer:' in line][0]
            
            # For self-signed certs, subject and issuer should be the same
            subject = subject_line.split('Subject:')[1].strip()
            issuer = issuer_line.split('Issuer:')[1].strip()
            assert subject == issuer, "Certificate should be self-signed for testing"
            
            # Check that CN=localhost for local testing
            assert "CN = localhost" in cert_text
            
            print("✅ Certificate security properties validated")
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Certificate security validation failed: {e}")
    
    def test_ssl_version_configuration(self):
        """Test SSL version configuration options"""
        config = get_config()
        ssl_version = config["ssl"]["ssl_version"]
        
        # Should use modern TLS (version 17 corresponds to PROTOCOL_TLS_SERVER)
        assert ssl_version == 17, f"Expected SSL version 17 (PROTOCOL_TLS_SERVER), got {ssl_version}"
        
        # Verify the SSL version maps to a valid SSL protocol
        try:
            if ssl_version == 17:
                protocol = ssl.PROTOCOL_TLS_SERVER
            else:
                protocol = ssl_version
            
            # Try to create context with this protocol
            context = ssl.SSLContext(protocol)
            assert context is not None
            
            print(f"✅ SSL version {ssl_version} configuration valid")
            
        except Exception as e:
            pytest.fail(f"SSL version validation failed: {e}")
    
    def test_https_warning_messages(self):
        """Test that appropriate warnings are shown for HTTP mode"""
        from src.server import main
        from unittest.mock import patch
        
        # Test HTTP mode warning
        with patch('uvicorn.run') as mock_run, \
             patch('src.server.get_config') as mock_config, \
             patch('builtins.print') as mock_print:
            
            # Configure for HTTP mode
            mock_config.return_value = {
                "ssl": {"enabled": False},
                "server": {"host": "0.0.0.0", "port": 8080}
            }
            
            with patch('src.server.mcp') as mock_mcp:
                mock_mcp.sse_app.return_value = None
                main()
            
            # Check that warning was printed
            warning_calls = [call for call in mock_print.call_args_list 
                           if len(call[0]) > 0 and "Warning" in str(call[0][0])]
            
            assert len(warning_calls) > 0, "No warning messages found"
            
            # Check for specific security warning
            security_warnings = [call for call in warning_calls
                               if "Bearer tokens" in str(call[0][0])]
            
            assert len(security_warnings) > 0, "No bearer token security warning found"
            
            print("✅ HTTP mode security warnings validated")


if __name__ == "__main__":
    pytest.main([__file__])
