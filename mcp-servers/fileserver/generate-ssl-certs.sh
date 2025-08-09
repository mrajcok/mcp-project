#!/bin/bash

# Generate SSL certificates for HTTPS testing
# This creates self-signed certificates - DO NOT use in production

echo "Generating self-signed SSL certificates for testing..."

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate private key
openssl genrsa -out ssl/server.key 2048

# Generate certificate signing request
openssl req -new -key ssl/server.key -out ssl/server.csr -subj "/C=US/ST=Test/L=Test/O=Test/OU=Test/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in ssl/server.csr -signkey ssl/server.key -out ssl/server.crt

# Set proper permissions
chmod 600 ssl/server.key
chmod 644 ssl/server.crt

echo "SSL certificates generated:"
echo "  Certificate: ssl/server.crt"
echo "  Private key: ssl/server.key"
echo ""
echo "To enable HTTPS, update config.yaml:"
echo "  ssl:"
echo "    enabled: true"
echo "    certfile: \"ssl/server.crt\""
echo "    keyfile: \"ssl/server.key\""
echo ""
echo "WARNING: These are self-signed certificates for testing only!"
echo "For production, use certificates from a trusted Certificate Authority."

# Clean up CSR file
rm ssl/server.csr
