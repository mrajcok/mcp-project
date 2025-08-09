# MCP File Server

## Description

This is an MCP (Model Context Protocol) File Server that provides secure file operations through authenticated HTTPS endpoints. The server supports various file operations like reading, writing, listing directories, and searching files while maintaining usage tracking and rate limiting with SSL/TLS encryption for secure token transmission.

## Features

- **HTTPS/SSL Support** - Secure bearer token transmission
- Bearer token authentication
- File and directory operations
- Usage tracking with SQLite
- Rate limiting and degraded state management
- Docker containerization
- Comprehensive test coverage

## Security

### HTTPS Configuration

**⚠️ Important: For production use, the server should run with HTTPS enabled to prevent bearer token interception.**

#### Quick Setup with Self-Signed Certificates (Testing Only)
```bash
# Generate self-signed certificates for testing
./generate-ssl-certs.sh

# Update config.yaml to enable SSL
ssl:
  enabled: true
  certfile: "ssl/server.crt"
  keyfile: "ssl/server.key"
```

#### Production SSL Setup
1. Obtain SSL certificates from a trusted Certificate Authority (Let's Encrypt, etc.)
2. Update `config.yaml`:
   ```yaml
   ssl:
     enabled: true
     certfile: "/path/to/your/certificate.crt"
     keyfile: "/path/to/your/private.key"
     ssl_version: 17  # PROTOCOL_TLS_SERVER
   ```

### Bearer Token Security
- Tokens are transmitted in HTTP Authorization headers
- HTTPS encryption prevents network sniffing
- Database-based token verification with role management

## Setup

1. Create a virtual environment:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure SSL (recommended):
   ```bash
   # For testing only
   ./generate-ssl-certs.sh
   # Edit config.yaml to enable SSL
   ```

4. Run the server:
   ```bash
   ./run.sh
   ```

## Docker

Build and run with Docker:
```bash
docker build -t mcp-fileserver .
docker run -p 8080:8080 mcp-fileserver
```

For HTTPS in Docker, mount your SSL certificates:
```bash
docker run -p 8080:8080 -v /path/to/ssl:/app/ssl mcp-fileserver
```

## Testing

The MCP File Server has comprehensive test coverage including unit tests, integration tests, and HTTPS security tests.

### Quick Start
```bash
# Run all tests
source venv/bin/activate
pytest

# Run with coverage report
pytest --cov=src --cov-report=html tests/
```

### Test Categories

#### Unit Tests
Test individual components and functions:

```bash
# Core server functionality
pytest tests/test_server.py -v

# Authentication and authorization
pytest tests/test_auth.py -v

# MCP tool handlers
pytest tests/test_handlers.py -v

# Configuration management
pytest tests/test_basic.py -v
```

#### Integration Tests
Test end-to-end functionality and component interaction:

```bash
# Practical integration tests (recommended)
pytest tests/test_integration_practical.py -v

# HTTPS MCP integration tests
pytest tests/test_https_mcp_integration.py -v
```

#### HTTPS/SSL Tests
Test SSL certificate generation and HTTPS security:

```bash
# Basic HTTPS configuration tests
pytest tests/test_https.py -v

# Certificate generation and validation
pytest tests/test_https_simple.py -v

# HTTPS integration tests
pytest tests/test_https_integration.py -v
```

#### Specific Test Scenarios

**Rate Limiting and Performance:**
```bash
# Test rate limiting and degraded state
pytest tests/test_server.py::test_rate_limiting_daily_limit -v
pytest tests/test_server.py::test_degraded_state_all_requests_429 -v
```

**Authentication and Security:**
```bash
# Bearer token authentication
pytest tests/test_auth.py::test_valid_token -v
pytest tests/test_auth.py::test_invalid_token -v

# HTTPS bearer token security
pytest tests/test_https_mcp_integration.py::TestHTTPSMCPIntegration::test_https_bearer_token_authentication -v
```

**MCP Tools:**
```bash
# File operations
pytest tests/test_handlers.py::test_create_file -v
pytest tests/test_handlers.py::test_read_text_file -v

# Directory operations  
pytest tests/test_handlers.py::test_list_directory -v
pytest tests/test_handlers.py::test_create_directory -v
```

### Test Configuration

The test suite uses `pytest.ini` to suppress third-party deprecation warnings while keeping relevant warnings visible. Tests are configured to:

- Use temporary databases for isolation
- Generate self-signed certificates for HTTPS testing
- Handle SSL handshake timing issues gracefully
- Provide detailed error reporting

### Coverage Analysis

Generate detailed coverage reports:

```bash
# HTML coverage report (opens in browser)
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing tests/

# Coverage threshold check (90%+ required)
pytest --cov=src --cov-fail-under=90 tests/
```

### Test Results Summary

- **Total Tests**: 115+ comprehensive tests
- **Coverage**: 90%+ code coverage
- **Categories**: Unit (70+), Integration (14+), HTTPS (17+), SSL (14+)
- **Success Rate**: 96%+ passing tests

### Troubleshooting Tests

**SSL/Certificate Issues:**
```bash
# Regenerate test certificates if needed
./generate-ssl-certs.sh

# Skip SSL timing-sensitive tests
pytest -m "not ssl_timing" tests/
```

**Database Issues:**
```bash
# Clean test databases
rm -f tests/test_*.db data/test_*.db

# Run with fresh database
pytest tests/test_auth.py --forked
```

**Verbose Debugging:**
```bash
# Maximum verbosity with output capture disabled
pytest -vvv -s tests/test_specific_test.py

# Show local variables on failure
pytest --tb=long tests/
```

### Expected Test Warnings

The test suite may display some expected warnings from third-party libraries that are safe to ignore:

**Websockets Deprecation Warnings:**
```
DeprecationWarning: websockets.legacy is deprecated
DeprecationWarning: websockets.server.WebSocketServerProtocol is deprecated
```
*These warnings come from uvicorn's websocket implementation and will be resolved when uvicorn updates to newer websockets versions.*

## Configuration

Edit `src/config.yaml` to configure:
- Allowed directories
- Rate limits
- Database paths and admin users (tokens are stored in the database)

### Override configuration (YAML-only)

This project uses layered YAML files for configuration. Environment-variable overrides and .env files are not used.

Precedence (highest first):
1) `CONFIG_OVERRIDE=/absolute/path/to/override.yaml`
2) `src/config.local.yaml` (if present)
3) `src/config.yaml` (base)

Overrides are deep-merged: nested dictionaries are merged; scalars/lists replace base values.

Examples:

Create `src/config.local.yaml` next to `src/config.yaml`:
```yaml
# src/config.local.yaml
rate_limit:
  daily_requests: 500
allowed_directories:
  - "/data"
  - "/tmp"
```

Or specify an external override file at runtime:
```bash
CONFIG_OVERRIDE=/path/to/override.yaml ./run.sh
```

Docker:
```bash
docker run -p 8080:8080 \
  -v /host/override.yaml:/app/src/config.local.yaml \
  mcp-fileserver
```
