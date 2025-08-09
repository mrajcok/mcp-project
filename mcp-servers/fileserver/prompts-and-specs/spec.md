### Developer-Ready Specification for MCP File Server

---

#### **1. Overview**

The MCP File Server is a secure and efficient server designed to handle a predefined set of filesystem operations over a network using the MCP protocol. The server will provide robust functionality for file and directory management while ensuring security, maintainability, and compatibility with existing MCP tools and systems.

---

#### **2. Requirements**

##### **Core Features**
- Support for filesystem operations:
  - Listing directories.
  - Reading file metadata.
  - Reading, creating, appending, and managing files and directories.
- Compatibility with the MCP protocol for all operations.
- Expose files and directories as MCP resources and actions.

##### **Security**
- HTTPS transport for secure communication.
- Bearer token authentication for all requests.
  - user ID included in requests
- Role-based permissions for filesystem operations.
- Logging of all operations for auditing purposes.
- User usage and monitoring
- degraded state handling if rate limits are exceeded

##### **Integration**
- Provide a clean API for clients to interact with the MCP server.
- Ensure compatibility with existing MCP tools and systems.
- Use resources like `/resources/file` and `/resources/dir` for reading and tools like `/tools/create_file` for actions.

##### **Configuration**
- Use a YAML file to configure server settings, such as allowed directories and administrators
- Bearer token should be in an .env file for local development and a docker secret for docker swarm deployment

##### **Deployment**
- Local development and Dockerized for easy deployment and testing.
- Include a `run.sh` script for local development setup.
- Support configuration for different environments (development, production).

---

#### **3. Architecture**

- **Programming Languages**:
  - Python 3.12 in a virtual environment for dependency management.

- **Frameworks and Tools**:
  - Use **FastMCP 2.0** (https://gofastmcp.com) for implementing the MCP protocol.
  - Minimal dependencies to ensure simplicity and maintainability.
  - sqlite database for tracking daily usage stats per user

##### **Directory Structure**
```
mcp-project/
├── mcp-servers/
│   ├── fileserver/
│   │   ├── data/
│   │   │   ├── usage.db           # SQLite database for tracking user usage
│   │   ├── src/
│   │   │   ├── server.py          # Main server implementation
│   │   │   ├── auth.py            # Authentication and authorization logic
│   │   │   ├── handlers/          # Handlers for MCP tools and resources
│   │   │   ├── config.yaml        # Configuration file
│   │   │   └── utils.py           # Utility functions
│   │   ├── tests/
│   │   │   ├── test_server.py     # Unit tests for server functionality
│   │   │   ├── test_auth.py       # Unit tests for authentication
│   │   │   └── test_handlers.py   # Unit tests for MCP handlers
│   │   ├── Dockerfile             # Docker configuration
│   │   ├── run.sh                 # Script for local development
│   │   └── README.md              # Project documentation
```

##### **Data Flow**
1. **Request Handling**: MCP requests are received and routed to the appropriate handler.
2. **Authentication**: Bearer tokens are validated, and user roles are checked.
3. **Filesystem Operations**: Handlers perform the requested operation (e.g., reading a file, listing a directory).
4. **Response**: Results are returned in MCP-compliant format.

---

#### **4. Data Handling**

- **Input Validation**:
  - Validate all inputs (e.g., file paths, patterns) to prevent injection attacks.
  - Ensure paths are within allowed directories.

- **Output Formatting**:
  - Return data in MCP-compliant format.
  - Include metadata (e.g., file size, permissions) where applicable.

- **Usage Tracking**:
  - Track user-specific metrics such as the number of requests, data transferred, and resource usage, per day, in an sqlite database.
  - Data should be kept for a configurable amount of time, default of 30 days.

- **Error Handling**:
  - Return appropriate MCP error codes for invalid requests (e.g., unauthorized access, file not found).
  - Log all errors with detailed context for debugging.

---

#### **5. Error Handling Strategies**

- **Authentication Errors**:
  - Return `401 Unauthorized` for invalid tokens.
  - Log failed authentication attempts.

- **Filesystem Errors**:
  - Return `404 Not Found` for missing files or directories.
  - Return `403 Forbidden` for unauthorized access.
  - Handle unexpected errors gracefully with `500 Internal Server Error`.

- **Validation Errors**:
  - Return `400 Bad Request` for invalid inputs (e.g., malformed paths).

- **Rate-Limiting**:
  - Enforce per-user rate limits based on their usage patterns
  - When any user exceeds their rate limit, log a critical error and have the server enter the degraded state, as defined below.

- **Degraded State**:
  - When in the degraded state, all requests must return `429 Too Many Requests`. The server must be manually restarted to exit the degraged state.

---

#### **6. Testing Plan**

##### **Unit Tests**
- Test each MCP tool and resource handler independently.
- Validate input handling, authentication, and error responses.

##### **Integration Tests**
- Simulate end-to-end MCP requests to ensure proper routing and response formatting.
- Test interactions between authentication, handlers, and filesystem operations.

##### **Security Tests**
- Verify HTTPS enforcement and token validation.
- Test role-based access control for all operations.

##### **Performance Tests**
- Measure response times for large directory listings and file operations.
- Test server behavior under concurrent requests.

##### **Test Coverage**
- Aim for 90%+ code coverage using tools like `pytest` and `coverage.py`.

---

#### **7. MCP Tools**

- **read_text_file**  
  Read the contents of a file as text. Always treats the file as UTF-8 text regardless of extension.  
  **Inputs**:  
    - `path` (string): File location.  
    - `head` (number, optional): First N lines.  
    - `tail` (number, optional): Last N lines.  

- **create_file**  
  Create a new file if it doesn't already exist.  
  **Inputs**:  
    - `path` (string): File location.  
    - `content` (string): File content.  

- **append_file**  
  Append contents to a file.  
  **Inputs**:  
    - `path` (string): File to edit.  
    - `content` (string): Content to append.  

- **create_directory**  
  Create a new directory or ensure it exists.  
  **Input**:  
    - `path` (string): Directory location.  
  Creates parent directories if needed. Succeeds silently if the directory already exists.  

- **list_directory**  
  List the contents of a directory.  
  **Input**:  
    - `path` (string): Directory location.  
  **Returns**:  
    - List of files and directories in the specified path.  
    - Each entry includes:  
      - `name`  
      - `type` (file/directory)  
      - `size` (for files)  
      - `modified time`  
      - `permissions` (read/write/execute)  

- **find_files**  
  Recursively search for files or directories.  
  **Inputs**:  
    - `path` (string): Starting directory.  
    - `pattern` (string): Search pattern.  
    - `excludePatterns` (string[]): Patterns to exclude (supports glob formats).  
  **Returns**:  
    - Full paths to matches.  

- **grep_files**  
  Search for text in files.  
  **Inputs**:  
    - `path` (string): Directory to search.  
    - `pattern` (string): Text pattern to match.  
    - `excludePatterns` (string[]): Patterns to exclude (supports glob formats).  
  **Returns**:  
    - List of files containing the pattern, with line numbers and the matched line content.  

- **get_file_info**  
  Get detailed metadata for a file or directory.  
  **Input**:  
    - `path` (string): File or directory location.  
  **Returns**:  
    - `size`  
    - `creation time`  
    - `modified time`  
    - `access time`  
    - `type` (file/directory)  
    - `permissions`  

- **list_allowed_directories**  
  List all directories the server is allowed to access.  
  **No Input Required**  
  **Returns**:  
    - Directories that the server can read/write from.

- **get_user_usage_stats**  
  Retrieve usage statistics for the authenticated user.  
  **No Input Required**  
  **Returns**:  
    - `requests_made` (number): Total number of requests made by the user per day
    - `data_transferred` (number): Total data transferred (in bytes) per day.  
    - `rate_limit_remaining` (number): Remaining requests allowed within the current rate limit window.  

- **get_usage_stats**  
  Retrieve usage statistics for the server.
  Only administrators can run this tool.
  **No Input Required**  
  **Returns**:  
    - `requests_made` (number): Total number of requests made per day
    - `data_transferred` (number): Total data transferred (in bytes) per day.  
    - `rate_limit_remaining` (number): Remaining requests allowed within the current rate limit window.  
---
