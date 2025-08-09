Below is a structured approach for planning, iterating, and ultimately generating the prompts for a code-generation LLM to implement the MCP File Server in a test-driven, incremental manner. This answer is organized as follows:

    High-Level Blueprint of All Phases
    First Round of Breakdowns (iterative chunks)
    Second (Deeper) Round of Breakdowns
    Final Prompt Series for Code Generation

Each prompt is separated in Markdown, enclosed in code blocks, and labeled appropriately. The goal is for each prompt to build on the code from the previous prompt, ensuring there is no orphaned or unused code.

1. High-Level Blueprint of All Phases

    Environment Setup & Project Skeleton
        Create virtual environment, directory structure, and basic placeholders (e.g., README, run.sh).
        Initialize testing framework.

    Minimal Server & Health Endpoint (TDD)
        Start with a simple “health check” route.
        Write a failing test for the route, implement minimal server to pass the test.

    Configuration Loading (config.yaml & environment variables)
        Write tests for reading from config and environment variables.
        Implement logic to load server settings (allowed directories, environment settings, etc.).

    Basic Authentication & Authorization
        Write tests for bearer token checking.
        Implement authentication logic that checks for valid tokens and user roles.

    SQLite Usage Tracking & Basic Rate-Limiting Framework
        Write tests to ensure each request is logged with user ID and usage stats in an SQLite database (usage.db).
        Implement minimal logic to store and retrieve usage data, but do not enforce limits yet.

    MCP Tools & Resource Handlers (Incremental TDD per Tool)
    a) list_directory
    b) create_directory
    c) create_file
    d) append_file
    e) read_text_file
    f) find_files
    g) grep_files
    h) get_file_info
    i) list_allowed_directories
    j) get_user_usage_stats
    k) get_usage_stats (administrators only)
        Each tool has:
            A failing test.
            Implementation to pass that test.

    Rate-Limiting & Degraded State
        Write tests to ensure that when a user exceeds a rate limit, the server enters a degraded state (returns 429).
        Implement logic for enforcing daily usage quota and degrade behavior.

    Dockerization & Final Integration
        Write integration tests for the Docker environment.
        Finalize Dockerfile, run.sh, and environment variable usage.
        Perform final checks and integration tests.

2. First Round of Breakdowns (Iterative Chunks)

    Chunk A: Project Setup & Basic Testing
        Virtual environment creation, directory structure, initial test framework setup.

    Chunk B: Minimal Server with TDD
        Implement a health-check route at "/health".
        Ensure “test_server.py” covers health endpoint.

    Chunk C: Configuration Management
        Implement code to read "config.yaml" and environment variables.
        Validate placeholders for allowed directories, environment modes, etc.

    Chunk D: Authentication & Authorization
        Add “auth.py” with token validation logic.
        Write tests for valid/invalid tokens, user roles.

    Chunk E: Usage Tracking
        Create “usage.db”, track requests in an SQLite table.
        Write tests for usage increments per request.

    Chunk F: Implement Each MCP Tool in Sequence
        For each tool: add test → implement logic → pass test.

    Chunk G: Rate-Limiting & Degraded State
        Write failing tests for usage thresholds.
        Implement logic to degrade (all 429) if threshold is exceeded.

    Chunk H: Docker & Final Integration
        Provide Dockerfile and container-based tests.
        Final review and documentation updates.

3. Second (Deeper) Round of Breakdowns

Here we break each chunk into smaller, test-friendly steps.
Chunk A: Project Setup & Basic Testing

A.1 Create directory structure according to the specification.
A.2 Initialize git repository and add a README.
A.3 Create a Python virtual environment.
A.4 Install testing frameworks (pytest, coverage).
A.5 Verify tests can run (placeholder test).
Chunk B: Minimal Server with TDD

B.1 Write a failing test in "test_server.py" for a GET /health endpoint.
B.2 Implement minimal "server.py" with "/health" route.
B.3 Confirm the test passes.
Chunk C: Configuration Management

C.1 Write a test to verify config loads from "config.yaml".
C.2 Write a test to verify environment variable overrides.
C.3 Implement "utils.py" or config loader code.
C.4 Confirm all config tests pass.
Chunk D: Authentication & Authorization

D.1 Write tests in "test_auth.py" for valid/invalid bearer tokens.
D.2 Implement "auth.py" to parse tokens, verify user roles.
D.3 Integrate with "server.py" routes (401 if invalid).
D.4 Confirm tests pass.
Chunk E: Usage Tracking

E.1 Write tests in "test_server.py" for usage increment on each request.
E.2 Create "usage.db" in /data.
E.3 Implement usage increment logic in "server.py" or "auth.py".
E.4 Confirm usage tests pass.
Chunk F: Implement Each MCP Tool in Sequence

(Each sub-step is: test → implement → pass)

F.1 list_directory
F.2 create_directory
F.3 create_file
F.4 append_file
F.5 read_text_file
F.6 find_files
F.7 grep_files
F.8 get_file_info
F.9 list_allowed_directories
F.10 get_user_usage_stats
F.11 get_usage_stats
Chunk G: Rate-Limiting & Degraded State

G.1 Write tests for usage threshold in "test_server.py".
G.2 Implement logic to degrade (maintain a global or DB-based “degraded” flag).
G.3 Confirm 429 is returned if in degraded state.
Chunk H: Docker & Final Integration

H.1 Write a Dockerfile and run.sh.
H.2 Write tests/build checks for Docker.
H.3 Final integration testing across all features.
H.4 Document usage in README, finalize coverage reports.
4. Final Prompt Series for Code Generation

Below are the prompts you can feed into a code-generation LLM (one by one) to build the project incrementally. Each prompt is presented in a Markdown code block, labeled accordingly. Provide the LLM each prompt in sequence to progressively construct and test the MCP File Server.
Prompt A1: Create Project Structure and Basic Test Setup

You are building the MCP File Server.  
1. Create the following directory structure (if any directories are missing, create them):  

mcp-project/
└── mcp-servers/
    └── fileserver/
        ├── data/
        │   ├── usage.db           # SQLite (will be populated later)
        ├── src/
        │   ├── server.py          
        │   ├── auth.py            
        │   ├── handlers/          # For MCP tools
        │   ├── config.yaml        # Configuration file
        │   └── utils.py           
        ├── tests/
        │   ├── test_server.py     
        │   ├── test_auth.py       
        │   └── test_handlers.py   
        ├── Dockerfile             
        ├── run.sh                 
        └── README.md              

2. Initialize a Python virtual environment (Python 3.12).  
3. Initialize a “requirements.txt” or “pyproject.toml” and include:
   - pytest
   - coverage
   - fastapi (if needed, or the minimal dependencies for FastMCP)
   - fastmcp==2.0
   - pyyaml
   - sqlite3 (builtin in Python, but note usage)
4. In “README.md”, briefly describe the project.  
5. Create a placeholder test in “tests/test_server.py” that always passes.  

Print all created/modified files to the console.  
Create no orphaned code or references; just the skeleton and placeholders.

Prompt B1: Write Failing Test for Health Endpoint

Now, write a failing test in test_server.py for a simple GET /health endpoint in server.py.  
1. The test should expect a 200 response when calling /health.  
2. The body of the response should be JSON with key "status" set to "ok".  
3. Run the test to confirm it fails (since server.py has no implementation yet).  
4. Print all updated code.

Prompt B2: Implement Minimal Server with /health Endpoint

Implement the minimum code in server.py to pass the failing /health endpoint test.  
1. Use FastMCP or minimal usage of FastAPI-like approach, or whichever minimal approach to stand up a server that handles /health.  
2. Ensure the route /health returns {"status": "ok"}.  
3. Confirm the test now passes.  
4. Print all updated server.py and any relevant code changes.

Prompt C1: Test for Configuration Loading

Add two tests in a new file or existing test: “test_utils.py” or keep it in “test_server.py”:  
1. One test to verify that loading config.yaml populates the expected fields (e.g., "allowed_directories").  
2. Another test to verify environment variable overrides.  

Both tests should fail because we haven’t implemented config logic.  
Print the updated test file(s).

Prompt C2: Implement Configuration Management

Implement configuration loading logic in utils.py (or a dedicated config loader).  
1. Load config.yaml.  
2. If environment variables (e.g., ALLOWED_DIRECTORIES) are set, override the config.  
3. Provide a get_config() function returning a dictionary.  
4. Make sure the tests now pass.  
Print the updated code and confirm passing tests.

Prompt D1: Write Tests for Authentication

In test_auth.py, write tests for bearer token authentication.  
1. A test for a valid token provided via an Authorization header "Bearer <token>".  
2. A test for an invalid token.  
3. A test for missing token.  
Expect 401 Unauthorized where appropriate.  
These tests should fail since we haven’t implemented auth.py logic yet.  
Print the updated test_auth.py.

Prompt D2: Implement Authentication & Authorization

Implement bearer token verification in auth.py.  
1. A function verify_token(token: str) -> (bool, user_role).  
2. Return True, role if token is valid, otherwise False, None.  
3. In server.py, integrate verifying tokens for each request. Return 401 if invalid.  
4. Confirm the tests pass.  
Print the updated auth.py and any relevant changes in server.py.

Prompt E1: Write Test for Usage Tracking

In test_server.py, write tests that confirm each request increments usage in usage.db:  
1. A test that ensures usage.db is updated with the user ID and request count.  
2. Use an in-memory or temporary file for usage.db to keep tests isolated.  
3. Expect a usage count that increments per request.  
These tests should fail since usage logic is not implemented yet.  
Print updated test_server.py.

Prompt E2: Implement Basic Usage Tracking

Implement usage tracking in server.py:
1. On each authenticated request, increment a usage counter for that user in sqlite (usage.db).  
2. Store date-based usage so we can track daily usage.  
3. Ensure the new usage count is saved properly.  
4. Confirm tests pass.  
Print updated code and confirm passing tests.

Prompt F (Repeat for Each MCP Tool)

You will repeat the same pattern for each of the MCP tools. Below is a template—substitute each specific tool name and functionality:
Prompt F1 (Test for list_directory)

Write a failing test in test_handlers.py for the MCP tool list_directory.  
1. The test calls an endpoint, e.g., /tools/list_directory, with a JSON body that includes a "path".  
2. It expects a JSON response listing the files and directories at that path.  
3. The test should fail since this is not implemented.  
Print the test code.

Prompt F2 (Implement list_directory)

Implement the list_directory MCP tool in handlers/list_directory.py (or inline in server.py if you prefer).  
1. It reads the "path" from the request.  
2. Returns a JSON object with fields: name, type, size, modified time, permissions for each item.  
3. Make sure the test passes.  
Print the updated handler and any changes to server.py or other files.

You would repeat the above two prompts (a failing test and then an implementation) for each of these tools:

    create_directory
    create_file
    append_file
    read_text_file
    find_files
    grep_files
    get_file_info
    list_allowed_directories
    get_user_usage_stats
    get_usage_stats

Be sure each tool has a failing test first, then an implementation. The pattern is:

    “<ToolName> Test” prompt
    “<ToolName> Implementation” prompt

Prompt G1: Write Test for Rate-Limiting & Degraded State

Write tests in test_server.py for rate-limiting and degraded state:  
1. Simulate multiple requests from the same user until they exceed a daily limit (e.g., 1000 requests).  
2. Expect the server to enter a degraded state, returning 429 for all subsequent requests.  
3. Tests should fail now.  
Print the test.

Prompt G2: Implement Rate-Limiting & Degraded State

Implement the logic to track daily usage threshold in usage.db.  
1. If a user’s usage exceeds the threshold, set a global "degraded" flag in the DB or server memory.  
2. Once degraded, all requests return 429.  
3. Confirm the tests for rate-limiting now pass.  
Print the updated code.

Prompt H1: Docker & Final Integration

Add the Dockerfile and run.sh logic to containerize and run the MCP File Server:  
1. Dockerfile should install dependencies, copy code, and run the server on port 8080.  
2. run.sh for local dev (activates venv, runs server).  
3. Write a final integration test (in test_server.py or a new test_integration.py) that spins up the server (docker or local) and exercises a few calls.  
Print the Dockerfile, run.sh, and any integration tests. Confirm all tests pass.

Prompt H2: Cleanup & Final Review

Perform final cleanup:  
1. Remove unused imports, code, or variables.  
2. Ensure README.md is updated with usage instructions.  
3. Confirm 90%+ coverage by running coverage.  
4. Summarize the final structure and all tests.  
Print a final summary of changes and confirm no orphan code remains.

Conclusion

Following the above prompts in order will help you build out the MCP File Server in small, testable increments. Each prompt produces working, integrated code, ensuring there is no unused or orphaned code. By the end, you will have a complete, Dockerized MCP File Server implementing the specified features with robust testing.
