# MCP Servers

This directory contains custom Model Context Protocol (MCP) servers.

## 🏗️ Architecture

Each MCP server is a standalone service that implements the MCP protocol to provide specific functionality for an MCP Host/AI agent. The servers use HTTPS transport for both local development and Docker Swarm deployment.

## 🔒 Security Framework

MCP servers follow consistent security practices:

### ✅ Standard Security Features

- **Input Validation** - All parameters validated via FastMCP type system
- **Path Restrictions** - File operations limited to allowed directories  
- **Container Isolation** - Each server runs in isolated Docker containers
- **Read-Only Design** - Default to read-only operations when possible
- **Error Handling** - Secure error messages without sensitive data exposure

### 🔧 Security Configuration

- **Environment Separation** - Different configs for development vs production
- **Resource Limits** - Configurable limits on file sizes and request counts
- **Access Control** - Directory-based access restrictions
- **Transport Security** - All communication between servers and clients uses HTTP transport, secured for both local development and Docker Swarm deployment.

```
mcp-servers/
├── file-server/          # Python-based file operations server
└── [future servers can be added here]
```

## 🔧 Available Servers

### 📁 File Server (`file-server/`)
**Status:** ✅ Production Ready

A Python-based MCP server providing secure read-only file and directory operations.

**Key Features:**
- Read file contents with encoding detection
- Directory listing with metadata
- File information and statistics
- Secure path validation
- HTTP transport for containerized deployment

**Technology:** Python 3.12 + FastMCP + FastAPI

See [file-server/README.md](file-server/README.md) for detailed documentation.

## 🚀 Quick Start

1. **Choose a server:**
   ```bash
   cd mcp-servers/fileserver  # or other server directory
   ```

2. **Run locally:**
   ```bash
   ./run.sh
   ```

3. **Test the server:**
   ```bash
   curl -i http://localhost:3001/sse
   ```
   You should get a 401 Unauthorized response if the server is running correctly
   since no bearer token is provided.

## 🔗 MCP Protocol Support

All servers implement the Model Context Protocol specification:

- **HTTP Transport** - Primary protocol for both local development and production deployment
- **Tool Discovery** - Automatic registration of available tools
- **Error Handling** - Standardized MCP error responses
- **Type Safety** - Strong typing for all tool parameters

### Best Practices

- **Security First** - Validate all inputs and restrict file/network access
- **Error Handling** - Provide clear, actionable error messages
- **Documentation** - Include comprehensive README.md for each server
- **Testing** - Comprehensive unit and integration tests are included for all core functionality, including health checks and error handling
- **Configuration** - Use environment variables for deployment settings

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [MCP SDK for Python](https://github.com/modelcontextprotocol/python-sdk)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Python Best Practices](https://docs.python-guide.org)
