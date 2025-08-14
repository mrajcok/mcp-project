## **Detailed Step-by-Step Blueprint and Iterative Plan**

Below is a complete roadmap for building this AI agent web application according to the requirements and specification. First, you will see a high-level blueprint. Next, we will break it into smaller, iterative chunks. Finally, we will take those chunks and produce pairs of TDD prompts (one for the tests, one for the implementation).

---

### 1) High-Level Blueprint

1. **Project & Environment Setup**  
   - Initialize a new Git repository.  
   - Create a Python 3.12 virtual environment (e.g., using `venv`).  
   - Install baseline dependencies:  
     - Flask, Dash, Plotly (for the web interface).  
     - ldap3 (for LDAP).  
     - sqlite / SQLAlchemy or Flask-SQLAlchemy (for DB).  
     - Pydantic AI + OpenAI (for LLM).  
     - FastMCP 2.0 (for MCP host/clients).  
   - Create a basic `run.sh` script to start the local server.  

2. **Configuration Loader**  
   - Implement a YAML-based config loader that loads from a file (e.g., `config.yaml`).  
   - Validate presence of keys like `authorized_users`, `admin_users`, `mcp_servers`, `confirmation_required_tools`, etc.  
   - Fail fast on missing/invalid config.  

3. **Database Initialization**  
   - Create SQLite schema with tables for `users`, `chat_sessions`, `chat_messages`, `tool_invocations`, etc.  
   - Implement a simple migration or schema creation script that sets up these tables.  

4. **User Model & Basic LDAP Authentication**  
   - Implement a `User` model in Python referencing the DB.  
   - Add code to authenticate users via ldap3 (use a mock in dev).  
   - Respect the `authorized_users` list from config.  
   - Handle the lockout after 3 failed attempts for 15 minutes.  

5. **Bearer Tokens & Session Management**  
   - Generate bearer tokens upon successful login; store them in DB.  
   - Ensure only 1 active token per user; new login invalidates old token.  
   - Set up a 12-hour idle timeout for tokens.  
   - Integrate Flask-Session to track server-side sessions in SQLite.  
   - Implement logic to forward the bearer token to MCP servers on behalf of the user.  

6. **Rate Limiting & Degraded State**  
   - Implement a per-user rate limit (50 operations / minute).  
   - If any user exceeds it, set a global flag for degraded state.  
   - In degraded state: only the login endpoint is accessible, all else returns HTTP 429.  
   - Provide concurrency limit (3 in-flight requests per user).  

7. **Chat Sessions**  
   - Create endpoints or routes for:  
     - Creating a new chat session.  
     - Listing user’s sessions.  
     - Deleting a session.  
     - Updating the session description.  
   - Add logic to store messages (user text + agent response).  
   - Purge data older than 30 days.  

8. **Tool Invocation Logic**  
   - Integrate with FastMCP 2.0 to connect to configured MCP servers.  
   - For each user request, parse references to `#tool_name`.  
   - For LLM-initiated tools that require confirmation, prompt user.  
   - Forward the user’s bearer token in each MCP request.  
   - Truncate tool output to 100k characters for storage.  

9. **LLM Integration**  
   - Use Pydantic AI with the OpenAI API.  
   - For each user message, run a “stateless” LLM call.  
   - The LLM call can propose tool usage.  
   - Add logic to handle user confirmation for “dangerous” tools.  

10. **Dash UI Scaffolding**  
    - Build the main Dash app:  
      - Layout with nav bar: Chat Agent, History, Admin, Username, Logout.  
      - Chat page with input box, streaming output area.  
      - Side panel listing MCP servers and status.  
      - History page to show past sessions and messages (paginated or infinite scroll).  

11. **Admin Page**  
    - Visible only to admins.  
    - Show usage metrics, graphs for chat volume, tool usage, rate-limit violations, etc.  

12. **Logging**  
    - Log all major events (login, logout, LLM calls, tool calls, degraded state) to stdout.  
    - Keep logs minimal for user content (store content in DB, but do not log it).  

13. **Retention & Cleanup**  
    - Implement automatic purging (daily or on startup) of old sessions (>30 days).  

14. **Integration & Final Polishing**  
    - End-to-end tests.  
    - Docker build container.  
    - Validate environment variable usage for secrets.  
    - Final checks on TLS/mTLS config for production.  
    - Final user acceptance testing.  

---

### 2) Breaking Down into Iterative Chunks

Below are the same major tasks, but split into smaller increments. Each increment is a functional milestone that can be developed/tested before moving on:

1. **Foundation & Repo Setup**  
   A. Initialize Git repository and project skeleton.  
   B. Create `pyproject.toml` or `requirements.txt`.  
   C. Basic directory structure (`chat_agent/` for app code, etc.).  

2. **Config Loader**  
   A. Introduce a `config.yaml`.  
   B. Write a Python module to parse and validate it.  

3. **Database Setup**  
   A. Create schema models for `users` (essential fields only).  
   B. Write migrations or a one-time schema creation routine.  
   C. Confirm DB connectivity with tests.  

4. **User Authentication**  
   A. Implement an LDAP-based `login(username, password)` function.  
   B. Enforce membership in `authorized_users`.  
   C. Implement lockout (3 failed attempts → 15m).  

5. **Bearer Tokens & Session**  
   A. Write a function to generate tokens (store in DB).  
   B. Invalidate previous tokens on new login.  
   C. Implement 12-hour idle timeout logic.  

6. **Rate Limiting & Degraded State**  
   A. Implement counting of operations per user.  
   B. If > 50 ops/min, set a global flag → degrade (429 for all but login).  

7. **Chat Sessions**  
   A. DB model for `chat_sessions` and `chat_messages`.  
   B. Endpoints/handlers for create, list, delete sessions.  
   C. Implement 30-day retention purge.  

8. **Tool Invocation**  
   A. Integrate FastMCP clients to reach servers from config.  
   B. Parse `#tool_name` from user messages.  
   C. If LLM tries to use a “dangerous” tool from config, require user confirmation.  

9. **LLM Integration**  
   A. Set up Pydantic AI with OpenAI.  
   B. For each user message, execute a single stateless call.  
   C. Return the result, possibly with recommended tool usage.  

10. **UI Scaffolding**  
   A. Build the initial Dash layout with nav bar.  
   B. Add chat page with input box + output area.  
   C. Add history page.  

11. **Admin Page**  
   A. Gate behind `is_admin` check.  
   B. Show usage metrics, graphs.  

12. **Logging**  
   A. Log to stdout: login, logout, LLM calls, tool calls, degrade events.  

13. **Cleanup / Automated Purging**  
   A. Cron-like or scheduled job for daily (or on startup) purges.  

14. **Final Integration, Docker, Testing**  
   A. Dockerfile & `docker-compose.yml` (or Swarm).  
   B. Final integration tests.  
   C. Documentation in README.  

We will now **split** these into still smaller, safer increments suitable for TDD.

---

### 3) Further Refinement into TDD-Friendly Steps

Below is an even more granular breakdown with the exact steps we want to test-drive. Each step will become **two prompts**: one for the test, one for the implementation.

1. **Foundation & Repo**  
   - (1A) Create empty project structure with `chat_agent/`.  
   - (1B) Add `.gitignore`, `requirements.txt`, and `pyproject.toml` (optional) with minimal dependencies.  
   - (1C) Validate that the environment can install dependencies.

2. **Config Loader**  
   - (2A) Write tests for a config parser that ensures required fields are present.  
   - (2B) Implement the config parser in code.  

3. **Database Setup**  
   - (3A) Write tests that confirm a `users` table can be created and read.  
   - (3B) Implement the DB schema initialization (SQLite).  

4. **User Model**  
   - (4A) Write tests for a `User` class with basic fields (`username`, `lockout_until`, etc.).  
   - (4B) Implement the `User` class and CRUD in DB.  

5. **LDAP Authentication**  
   - (5A) Write tests for a function `authenticate_user(username, password)` that uses mock LDAP.  
   - (5B) Implement the real LDAP logic (mock or real).  

6. **Lockout**  
   - (6A) Write tests ensuring 3 failed logins sets a lockout for 15m.  
   - (6B) Implement the logic checking attempts, storing timestamps.  

7. **Bearer Token Generation**  
   - (7A) Write tests that create a token, store it, and ensure only one active token per user.  
   - (7B) Implement the token logic.  

8. **Session & Idle Timeout**  
   - (8A) Write tests to confirm tokens expire after 12 hours of inactivity.  
   - (8B) Implement the idle timeout in code (check last activity).  

9. **Rate Limiting & Degraded State**  
   - (9A) Write tests that track user ops, fail after 50 ops in a minute → degrade.  
   - (9B) Implement the logic (global degrade flag).  

10. **Chat Sessions & Messages**  
   - (10A) Write tests for: session creation, message storage, 30-day purge.  
   - (10B) Implement session endpoints, DB schema, Purge routine.  

11. **Tool Invocation**  
   - (11A) Test parsing of `#tool_name` from user message; test user confirmation if “dangerous.”  
   - (11B) Integrate with FastMCP, do actual calls, store 100k-chars truncated output.  

12. **LLM Integration**  
   - (12A) Write tests that call a mock LLM (Pydantic AI) and check output handling.  
   - (12B) Implement stateless call to OpenAI.  

13. **Dash UI**  
   - (13A) Write tests (could be Cypress or Selenium) checking basic rendering, nav bar, etc.  
   - (13B) Implement the Dash layout, pages, session handling.  

14. **Admin Page & Logging**  
   - (14A) Write tests ensuring only admins can view metrics. Check logs for degrade events, etc.  
   - (14B) Implement admin page with usage metrics, logs to stdout.  

15. **Docker & Final Integration**  
   - (15A) Write tests for Docker build (maybe build is successful, container runs a health check).  
   - (15B) Final integration, tie up environment variable usage, confirm mTLS config placeholders are in place.  

Each of these “(nA) Test” and “(nB) Implementation” tasks will be a pair of prompts.

---

## **TDD Prompts**

Below is an example TDD workflow for each chunk. **Each step has two prompts**: one for the test (written in detail), and one for the implementation. The code-generation LLM will first see the test prompt, generate test code, and then (once that test code is validated or reviewed) see the implementation prompt to produce the solution.

Below is the raw Markdown for all prompts.  
> **Note**: The actual structure in your own project might vary slightly. But this is the recommended style for incremental TDD with separate test/implementation prompts.

---

### 1) Foundation & Repo

```text
# Prompt (1A) Test: Initialize Project Structure

**Objective**: Write a test that checks if the project structure is in place:
1. "chat_agent/" directory exists
2. There's a minimal "main.py" or similar inside.
3. There's a "requirements.txt" or "pyproject.toml" with minimal dependencies.

**Details**:
- We'll use Python's built-in tools or `pytest` to confirm the directory structure.
- We'll assume the code generation LLM can run a shell or check the file system.

**What to Test**:
- That "chat_agent/" is a valid directory.
- That the minimal file "chat_agent/__init__.py" or "main.py" exists.
- That "requirements.txt" or "pyproject.toml" references known packages like "Flask" or "Dash".

We can keep the test simple. The point is to ensure scaffolding is generated properly.
```

```text
# Prompt (1B) Implementation: Initialize Project Structure

**Objective**: Create the basic project skeleton so that the test above passes.
1. Create "chat_agent/" as a directory.
2. Place an empty "__init__.py" inside "chat_agent/".
3. Create a "main.py" with a simple "if __name__ == '__main__': pass".
4. Create a minimal "requirements.txt" or "pyproject.toml" with:
   - flask
   - dash
   - pyyaml (for config)
   - any other minimal libs we foresee
5. Ensure the repository is initialized with "git init" if needed.
```

---

### 2) Config Loader

```text
# Prompt (2A) Test: Config Parser

**Objective**: Write a unit test for a config parser function, e.g. "load_config(path)".
**We expect**:
- The function raises an error if required fields are missing:
  - "authorized_users" (list)
  - "admin_users" (list)
  - "mcp_servers" (list)
  - "confirmation_required_tools" (list)
  - etc.
- The function returns a config object/dict if all fields are valid.

**Implementation Hints**:
- We'll likely use "pyyaml" or similar for YAML loading.
- We'll define a custom exception for invalid config or just raise "ValueError".
- Config structure is well-defined, so test each required key presence.
```

```text
# Prompt (2B) Implementation: Config Parser

**Objective**: Implement the "load_config(path)" function so that the test passes.
1. Use "pyyaml" to open and parse the file.
2. Validate the presence of the required keys.
3. If missing, raise ValueError with a clear message.
4. If everything is present, return a dict or a pydantic model (developer choice).
5. Put this function in "chat_agent/config.py" (for instance).
```

---

### 3) Database Setup

```text
# Prompt (3A) Test: Database Initialization

**Objective**: Write a test to ensure we can initialize an SQLite database with minimal schema.
**We expect**:
- A "users" table is created.
- The test can insert a row and retrieve it.
- The DB file is located in some default path (e.g., "db.sqlite") or ephemeral test path.

**Implementation Hints**:
- We can use "Flask-SQLAlchemy" or "sqlalchemy" directly.
- The test might run a function "init_db()" or "migrate()" that sets up the schema.
```

```text
# Prompt (3B) Implementation: Database Initialization

**Objective**: Implement the DB schema creation code so that the test from (3A) passes.
1. Create a module "chat_agent/db.py" with an "init_db()" function.
2. Use SQLAlchemy or Flask-SQLAlchemy. 
3. Define at least one table: "users" with columns "id" (int PK), "username" (string).
4. The function should create all tables if they don't exist.
5. The test can verify by adding a sample user and querying it back.
```

---

### 4) User Model

```text
# Prompt (4A) Test: User Model

**Objective**: Create a test for a "User" Python class that:
- Maps to the "users" table
- Has fields: "id", "username", "lockout_until", "token", etc.
- Has methods for CRUD or static constructor "User.create()" or something similar.

**We expect**:
- We can create a new user in Python, commit to DB, query it back.
- lockout_until can be null or a datetime.
```

```text
# Prompt (4B) Implementation: User Model

**Objective**: Implement the "User" class to pass the above test.
1. Define a SQLAlchemy model "User" in "chat_agent/models.py".
2. Ensure columns match specification: "id", "username", "lockout_until", "token", etc.
3. Provide a constructor or static method to create and persist the user.
4. Make sure to integrate with the existing DB session from (3B).
```

---

### 5) LDAP Authentication

```text
# Prompt (5A) Test: LDAP Authentication

**Objective**: Test a function "authenticate_user(username, password)" that:
- Uses a mock LDAP server or a mock in python to simulate success/failure.
- Checks if "username" is in "authorized_users" from config.
- Returns True if valid, False if invalid credentials or not authorized.

**We expect**:
- If the user is not in config, return False.
- If the credentials are incorrect, return False.
- If correct and authorized, return True.
- We do not handle lockout just yet in this test (that’s next).
```

```text
# Prompt (5B) Implementation: LDAP Authentication

**Objective**: Implement "authenticate_user(username, password)".
1. Load config from "load_config()".
2. Use "ldap3" or a mock for dev to attempt an LDAP bind (overridable in tests).
3. If bind succeeds and user is in config["authorized_users"], return True.
4. Otherwise, return False.
5. For local dev, possibly bypass real LDAP with a "MockLDAP" class.
```

---

### 6) Lockout

```text
# Prompt (6A) Test: Lockout

**Objective**: Test that after 3 failed login attempts for the same user+IP, "lockout_until" is set for 15 minutes in the DB. 
**We expect**:
- The test tries to authenticate 3 times with bad credentials.
- The system sets "lockout_until" field on the user.
- A 4th attempt is automatically rejected until the 15 minutes pass (simulate or check the field).
```

```text
# Prompt (6B) Implementation: Lockout

**Objective**: Implement the logic in "authenticate_user" or a wrapper:
1. Keep track of failed login attempts (e.g., in the DB or in memory).
2. After each failed attempt, increment a counter.
3. If the counter hits 3, set "lockout_until = now+15minutes".
4. If user is locked out, do not even check LDAP. Return False.
5. Reset counter on successful login.
```

---

### 7) Bearer Token Generation

```text
# Prompt (7A) Test: Bearer Token

**Objective**: Test a function "issue_token(user_id)" that:
- Generates a random token.
- Stores it in the user's DB entry or a separate table.
- Ensures that any previous token is invalidated.

**We expect**:
- The new token is non-empty and unique.
- The old token is cleared or marked invalid.
```

```text
# Prompt (7B) Implementation: Bearer Token

**Objective**: Implement the logic in "issue_token(user)" or similar:
1. Generate a random/opaque string (e.g., "secrets.token_hex(32)").
2. Assign user.token = new_token; user.save().
3. If user already had a token, override it.
4. Return the new token string.
```

---

### 8) Session & Idle Timeout

```text
# Prompt (8A) Test: Idle Timeout

**Objective**: Test that tokens expire if not used for 12 hours.
**We expect**:
- On each request, "last_activity_at" is updated for the user or token.
- If 12 hours pass, the token is considered invalid.

**Implementation Hints**:
- The test might artificially manipulate time or "last_activity_at" to simulate 12 hours.
- Attempt to use the token afterwards, expecting a failure.
```

```text
# Prompt (8B) Implementation: Idle Timeout

**Objective**: Implement the logic:
1. Each request includes the user's token → check DB's "last_activity_at".
2. If "now - last_activity_at > 12 hours", reject.
3. Otherwise, update "last_activity_at = now".
4. Possibly do this check in a middleware or decorator.
```

---

### 9) Rate Limiting & Degraded State

```text
# Prompt (9A) Test: Rate Limit & Degraded

**Objective**: Verify that we track user operations per minute.
**We expect**:
- If user does > 50 ops in 60s, app sets a global "DEGRADED" flag.
- Once "DEGRADED" is set, all requests except login return 429.
- The test also ensures concurrency limit (3 in-flight requests).
```

```text
# Prompt (9B) Implementation: Rate Limit & Degraded

**Objective**: Implement logic:
1. Maintain an in-memory or DB-based count of ops per user per 60s window.
2. If user hits 51, set `global_degraded = True` in a global or shared state.
3. If `global_degraded` is True, any request but login returns 429.
4. For concurrency limit, track how many requests are active for a user. If 3 are in flight, reject new ones with error.
```

---

### 10) Chat Sessions & Messages

```text
# Prompt (10A) Test: Chat Sessions & Messages

**Objective**: Verify we can:
1. Create a chat session.
2. Post user messages, store them in DB.
3. Retrieve messages for that session.
4. Delete session if needed.
5. Purge after 30 days.

**We expect**:
- Basic CRUD of chat sessions.
- Some test that artificially sets "last_activity_at" older than 30 days, calls "purge()" and sees data removed.
```

```text
# Prompt (10B) Implementation: Chat Sessions & Messages

**Objective**: Implement the code so the test passes:
1. Define models for "chat_sessions" and "chat_messages."
2. Provide endpoints or function calls to create, list, delete sessions.
3. A "purge_old_sessions()" function that checks last activity and deletes if 30 days old.
4. Integrate with DB commits.
```

---

### 11) Tool Invocation & Confirmation

```text
# Prompt (11A) Test: Tool Invocation

**Objective**: Test:
1. Recognizing `#tool_name` in user messages → no confirmation needed.
2. If the LLM requests a tool from "confirmation_required_tools", prompt user.
3. If user denies, do not call the tool.
4. On success, store the truncated output in DB.

**We expect**:
- Proper parsing of "tool_name".
- Truncation at 100k chars.
- Confirmation flow for dangerous tools.
```

```text
# Prompt (11B) Implementation: Tool Invocation

**Objective**: Implement tool-invocation logic:
1. Parse user messages for `#tool_name`.
2. If LLM asks for a tool that’s in the config list and not user-explicit, require explicit user approval.
3. Call the target MCP server with `bearer token` in the header.
4. Truncate output to 100k. Store in "tool_invocations" table.
5. Mark success/failure accordingly.
```

---

### 12) LLM Integration

```text
# Prompt (12A) Test: LLM Integration

**Objective**: Test a function "run_llm(user_input)" that:
1. Calls OpenAI (mock in test).
2. Returns the response text.
3. Possibly returns "recommended_tool" if the model suggests one.

**We expect**:
- A curated response from the mock LLM.
- No conversation context (stateless).
- If the LLM suggests a tool, this is exposed in the function return for the next step (like "tool_name": "read_text_file").
```

```text
# Prompt (12B) Implementation: LLM Integration

**Objective**: Implement "run_llm(user_input)":
1. Use Pydantic AI with OpenAI API.
2. Provide minimal prompt structure (since stateless).
3. Return the raw text. If the model can return structured data (like a "tool name"), parse it.
4. Ensure you handle rate-limiting "1 operation = 1 LLM call."
```

---

### 13) Dash UI

```text
# Prompt (13A) Test: Dash UI

**Objective**: Use an end-to-end or integration style test with a tool like Selenium or Cypress:
1. Ensure the main page loads.
2. Validate the nav bar has "Chat Agent," "History," "Admin" (if admin), "Username," "Logout."
3. Ensure there's an input field for messages and an area to display the output.

**We expect**:
- On visiting the root, if not authenticated, the user is redirected to a login page.
- If logged in, the chat page is accessible.
```

```text
# Prompt (13B) Implementation: Dash UI

**Objective**: Implement the basic Dash application:
1. Create "app.py" or "server.py" with the Dash instance.
2. Define the layout with a nav bar, chat page, history page, admin page placeholder.
3. Handle login flow (maybe via a separate Flask route or a Dash page).
4. Host on the default port (e.g., 8050).
```

---

### 14) Admin Page & Logging

```text
# Prompt (14A) Test: Admin & Logging

**Objective**: Test:
1. Only admin users can access "/admin."
2. The page shows usage stats or placeholders for them.
3. Logging is triggered on major events (login, degrade, LLM, tool calls).

**We expect**:
- Trying to load "/admin" as a non-admin → 403 or redirect.
- Admin can see basic usage metrics (faked for now).
- The logs in stdout contain the relevant event lines.
```

```text
# Prompt (14B) Implementation: Admin & Logging

**Objective**: Implement:
1. The admin layout in Dash that displays basic usage stats.
2. Use python’s "logging" or "print" to stdout for events. 
3. Gate the admin page behind an "is_admin" check in the session or DB user field.
4. Possibly show placeholders for usage graphs using Dash/Plotly.
```

---

### 15) Docker & Final Integration

```text
# Prompt (15A) Test: Docker Build & Integration

**Objective**: Test building a Docker image and running it:
1. Dockerfile that copies the code, installs dependencies, exposes port 8050.
2. "docker build" doesn't fail.
3. "docker run" starts the server, health endpoint ("/health") returns "OK".

**We expect**:
- The container runs, environment variables can be set for LDAP, OpenAI key, etc.
```

```text
# Prompt (15B) Implementation: Docker & Final Integration

**Objective**: 
1. Create "Dockerfile" with Python 3.12 base.
2. Copy the code, run "pip install -r requirements.txt".
3. Expose the port, define "CMD" to run the Dash app.
4. Possibly add a "/health" route that returns "OK".
5. Ensure any final environment-based config, e.g. secrets from env variables, is recognized.
6. Confirm the system is fully integrated: LDAP, DB, LLM, and MCP servers all accounted for in the final container.
```

---

## **Conclusion**

The above series of prompts (two per step) should guide a code-generation LLM to develop this system step by step, using **Test-Driven Development**. Each step builds upon the previous ones, ensuring no orphan code or incomplete integrations. By following this plan, you can grow the project **incrementally**, verifying correctness at each stage and minimizing surprises. 

This structure also encourages code reviews and refactoring between steps, giving you a safe, test-backed foundation for the entire AI agent application.