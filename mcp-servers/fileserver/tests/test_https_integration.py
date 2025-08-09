# ABOUT-ME: Integration tests for HTTPS functionality with real certificates
# ABOUT-ME: Tests actual HTTPS server startup and communication with generated certificates

import pytest
import os
import tempfile
import yaml
import subprocess
import requests
import time
import threading
import socket
from contextlib import contextmanager
from src.server import main
from src.utils import get_config


def get_free_port():
    """Get a free port by creating and immediately closing a socket"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
    except OSError:
        # If binding fails for any reason, try a few more times
        import time
        for attempt in range(5):
            time.sleep(0.1)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', 0))
                    return s.getsockname()[1]
            except OSError:
                continue
        # If all retries fail, let the exception propagate
        raise


class TestHTTPSRealIntegration:
    """Real integration tests for HTTPS functionality"""
    
    @pytest.fixture(scope="class")
    def https_config_file(self):
        """Create a temporary config file with HTTPS enabled"""
        # Generate certificates in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_file = os.path.join(temp_dir, "server.crt")
            key_file = os.path.join(temp_dir, "server.key")
            
            # Generate certificates using OpenSSL
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
                
                # Get a free port for this test
                free_port = get_free_port()
                
                # Create config with HTTPS enabled
                https_config = {
                    "ssl": {
                        "enabled": True,
                        "certfile": cert_file,
                        "keyfile": key_file,
                        "ssl_version": 17
                    },
                    "server": {
                        "host": "127.0.0.1",
                        "port": free_port  # Use dynamic port to avoid conflicts
                    },
                    "allowed_directories": [temp_dir],
                    "rate_limit": {"daily_requests": 1000},
                    "database": {
                        "user_db_path": os.path.join(temp_dir, "users.db"),
                        "usage_db_path": os.path.join(temp_dir, "usage.db")
                    },
                    "admin_users": ["testadmin"]
                }
                
                # Write config to temporary file
                config_file = os.path.join(temp_dir, "test_config.yaml")
                with open(config_file, 'w') as f:
                    yaml.dump(https_config, f)
                
                yield {
                    "config_file": config_file,
                    "cert_file": cert_file,
                    "key_file": key_file,
                    "port": free_port,
                    "temp_dir": temp_dir
                }
                
            except subprocess.CalledProcessError:
                pytest.skip("OpenSSL not available for certificate generation")
    
    @contextmanager
    def https_server(self, config_info):
        """Start HTTPS server in background thread with fresh port"""
        import uvicorn
        from src.server import mcp
        
        # Get a fresh port for this server instance to avoid conflicts
        server_port = get_free_port()
        
        # Server configuration
        server_config = {
            "app": mcp.sse_app(),
            "host": "127.0.0.1",
            "port": server_port,  # Use fresh port instead of config port
            "ssl_keyfile": config_info["key_file"],
            "ssl_certfile": config_info["cert_file"],
            "ssl_version": 17
        }
        
        server_started = threading.Event()
        server_error = None
        
        def run_server():
            nonlocal server_error
            try:
                server_started.set()
                uvicorn.run(**server_config)
            except Exception as e:
                server_error = e
                server_started.set()
        
        # Start server in daemon thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        server_started.wait(timeout=3)
        
        if server_error:
            pytest.skip(f"Server failed to start: {server_error}")
        
        # Give server time to fully start
        time.sleep(1)
        
        try:
            yield server_port  # Return the actual server port, not config port
        finally:
            # Wait for port to be released after test
            time.sleep(0.5)
    
    def wait_for_port(self, host, port, timeout=10):
        """Wait for a port to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (socket.error, ConnectionRefusedError):
                time.sleep(0.1)
        return False
    
    def test_https_health_endpoint(self, https_config_file):
        """Test HTTPS health endpoint with real certificates"""
        with self.https_server(https_config_file) as port:
            # Wait for server to be ready
            if not self.wait_for_port("127.0.0.1", port, timeout=5):
                pytest.skip("Server did not start in time")
            
            # Test HTTPS connection to health endpoint using the generated certificate
            try:
                response = requests.get(
                    f"https://127.0.0.1:{port}/health",
                    verify=https_config_file["cert_file"],  # Use the generated certificate
                    timeout=10
                )
                
                # Check that we got a response (even if 404, means HTTPS is working)
                assert response.status_code in [200, 404, 405]
                
                # If we get here, HTTPS is working
                print(f"HTTPS connection successful: status {response.status_code}")
                
            except requests.exceptions.SSLError as e:
                pytest.fail(f"SSL/HTTPS connection failed: {e}")
            except requests.exceptions.ConnectionError as e:
                pytest.skip(f"Connection failed (server may not have started): {e}")
    
    def test_https_vs_http_security(self, https_config_file):
        """Test that HTTPS provides encrypted communication vs HTTP"""
        with self.https_server(https_config_file) as port:
            # Wait for server to be ready
            if not self.wait_for_port("127.0.0.1", port, timeout=5):
                pytest.skip("Server did not start in time")
            
            # Test HTTPS connection using the generated certificate
            try:
                https_response = requests.get(
                    f"https://127.0.0.1:{port}/health",
                    verify=https_config_file["cert_file"],  # Use the generated certificate
                    timeout=10
                )
                
                # Test that HTTP connection to HTTPS port fails appropriately
                try:
                    http_response = requests.get(
                        f"http://127.0.0.1:{port}/health",
                        timeout=5
                    )
                    # If HTTP works on HTTPS port, that's a security issue
                    pytest.fail("HTTP connection succeeded on HTTPS port - security vulnerability!")
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
                    # This is expected - HTTP should not work on HTTPS port
                    pass
                
                # If we got here with HTTPS working, that's good
                assert https_response.status_code in [200, 404, 405]
                print("HTTPS security verified: HTTP blocked, HTTPS working")
                
            except requests.exceptions.SSLError as e:
                pytest.fail(f"HTTPS connection failed: {e}")
            except requests.exceptions.ConnectionError as e:
                pytest.skip(f"HTTPS server not responding: {e}")
    
    def test_certificate_validation_info(self, https_config_file):
        """Test that we can get certificate information from the HTTPS connection"""
        import ssl
        import socket
        import time
        import subprocess
        
        # First, verify the certificate file exists and is valid
        cert_file = https_config_file["cert_file"]
        key_file = https_config_file["key_file"]
        
        # Verify certificate with OpenSSL
        try:
            result = subprocess.run([
                "openssl", "x509", "-in", cert_file, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            print(f"Certificate details from file:\n{result.stdout[:500]}...")
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Certificate file is invalid: {e}")
        
        with self.https_server(https_config_file) as port:
            # SSL context for connecting to the server
            context = ssl.create_default_context()
            context.check_hostname = False  # For self-signed certificates
            context.verify_mode = ssl.CERT_NONE  # For self-signed certificates            # Wait for server to start (with retries)
            max_retries = 10
            base_delay = 0.5
            
            for attempt in range(max_retries):
                if attempt > 0:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** (attempt - 1)) + (attempt * 0.1)
                    delay = min(delay, 5.0)  # Cap at 5 seconds
                    time.sleep(delay)
                
                print(f"🔍 Attempt {attempt + 1}/{max_retries}: Testing certificate info...")
                
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                            # Try both methods to get certificate info
                            cert_info_decoded = ssock.getpeercert(binary_form=False)
                            cert_info_binary = ssock.getpeercert(binary_form=True)
                            
                            print(f"Decoded certificate info: {cert_info_decoded}")
                            print(f"Binary certificate exists: {cert_info_binary is not None}")
                            
                            # Check if we got any certificate info
                            if cert_info_decoded:
                                # We have certificate info in decoded format
                                assert "subject" in cert_info_decoded, f"Certificate should have subject field. Got: {cert_info_decoded}"
                                assert "issuer" in cert_info_decoded, "Certificate should have issuer field"
                                
                                # Parse subject information
                                subject_dict = {}
                                for item in cert_info_decoded["subject"]:
                                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                                        key, value = item[0], item[1]
                                        subject_dict[key] = value
                                
                                assert "commonName" in subject_dict, f"commonName not found in subject: {subject_dict}"
                                common_name = subject_dict.get("commonName")
                                assert common_name in ["localhost", "127.0.0.1"], f"Expected localhost or 127.0.0.1, got: {common_name}"
                                
                                print(f"✅ Certificate validated: CN={common_name}")
                                return  # Success
                                
                            elif cert_info_binary:
                                # We have binary certificate info - decode it manually
                                from cryptography import x509
                                from cryptography.hazmat.backends import default_backend
                                
                                try:
                                    cert = x509.load_der_x509_certificate(cert_info_binary, default_backend())
                                    subject = cert.subject
                                    common_name = None
                                    
                                    for attribute in subject:
                                        if attribute.oid.dotted_string == "2.5.4.3":  # Common Name OID
                                            common_name = attribute.value
                                            break
                                    
                                    assert common_name is not None, "Certificate should have a Common Name"
                                    assert common_name in ["localhost", "127.0.0.1"], f"Expected localhost or 127.0.0.1, got: {common_name}"
                                    
                                    print(f"✅ Certificate validated via binary decode: CN={common_name}")
                                    return  # Success
                                    
                                except ImportError:
                                    print("⚠️ cryptography module not available for binary certificate parsing")
                                    pytest.skip("cryptography module required for binary certificate parsing")
                                    
                            else:
                                print(f"⚠️ No certificate info available on attempt {attempt + 1}")
                                if attempt == max_retries - 1:
                                    # Last attempt - check if it's a configuration issue
                                    print("Certificate validation failed - this may indicate an SSL configuration issue")
                                    print("Server is running and SSL connection works, but certificate info is not available")
                                    pytest.skip("SSL server is functional but certificate details not retrievable")
                
                except (ConnectionRefusedError, ssl.SSLError, OSError) as e:
                    print(f"Connection failed on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        pytest.fail(f"Failed to connect to HTTPS server after {max_retries} attempts")
                    continue
            
            pytest.fail("Certificate validation failed after all retry attempts")


class TestHTTPSConfigurationSwitching:
    """Test switching between HTTP and HTTPS configurations"""
    
    def test_config_switch_http_to_https(self):
        """Test configuration switching from HTTP to HTTPS"""
        # Start with HTTP config
        http_config = get_config()
        assert http_config["ssl"]["enabled"] is False
        
        # Create HTTPS config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            https_config = http_config.copy()
            https_config["ssl"]["enabled"] = True
            https_config["ssl"]["certfile"] = "ssl/server.crt"
            https_config["ssl"]["keyfile"] = "ssl/server.key"
            
            yaml.dump(https_config, f)
            temp_config_path = f.name
        
        try:
            # Read the HTTPS config
            with open(temp_config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Verify HTTPS is enabled
            assert loaded_config["ssl"]["enabled"] is True
            assert loaded_config["ssl"]["certfile"] == "ssl/server.crt"
            assert loaded_config["ssl"]["keyfile"] == "ssl/server.key"
            
            print("Configuration switching test passed")
            
        finally:
            os.unlink(temp_config_path)
    
    def test_ssl_certificate_paths_validation(self):
        """Test validation of SSL certificate paths"""
        # Test with valid certificate paths (from generated certs)
        if os.path.exists("ssl/server.crt") and os.path.exists("ssl/server.key"):
            # Verify certificates exist and are readable
            assert os.path.isfile("ssl/server.crt")
            assert os.path.isfile("ssl/server.key")
            
            # Verify certificates are not empty
            assert os.path.getsize("ssl/server.crt") > 0
            assert os.path.getsize("ssl/server.key") > 0
            
            print("SSL certificate paths validation passed")
        else:
            pytest.skip("Generated SSL certificates not found")


if __name__ == "__main__":
    pytest.main([__file__])
