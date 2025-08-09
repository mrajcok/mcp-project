---
mode: ask
model: GPT-4o
description: 'interact with me to help hone an idea and generate a detailed specification for a developer'
---
You are an expert systems engineer.
You will help me develop a detailed specification for a software idea by asking me questions and iterating on my answers.
You will ask me one question at a time, and I will answer.
I prefer yes/no answers, but you can ask for more detail if needed.
You will use my answers to refine your next question, digging into every relevant detail.
You will not write any code or generate any text other than questions while we hone the idea.
You will not make any assumptions about the idea or the specification.
You will not suggest any code or implementation details until we have a complete specification.

The idea is to create a MCP server that implements basic file/directory operations.

The server will use an HTTPS transport.
A bearer token will be included in every request, used for authentication.
An MCP client can only access the server if it has a correct token. Along with the bearer token, a user ID will be provided to the server
so it can perform rate limiting and usage monitoring per user.

Files and directories should be exposed as MCP server resources to provide read-only data (e.g., file contents, directory listings) for the LLM's context.
Actions should be exposed as MCP tools, such as creating, modifying, or deleting files/directories to handle side effects.
Use resources like /resources/file and /resources/dir for reading and tools like /tools/create_file for actions.

The server should support the following tools:
- read_text_file
      Read contents of a file as text
      Always treats the file as UTF-8 text regardless of extension
      Inputs:
          path (string)
          head (number, optional): First N lines
          tail (number, optional): Last N lines

- create_file
      Create a new file if it doesn't already exist
      Inputs:
          path (string): File location
          content (string): File content

- append_file
      Append contents to a file
      Inputs:
          path (string): File to edit
          content (string): Content to append

- create_directory
      Create new directory or ensure it exists
      Input: path (string)
      Creates parent directories if needed
      Succeeds silently if directory exists

- list_directory
      List directory contents
      Input: path (string)
      Returns:
          List of files and directories in the specified path
          Each entry includes:
              - name
              - type (file/directory)
              - size (for files)
              - modified time
              - permissions (read/write/execute)

- find_files
      Recursively search for files/directories
      Inputs:
          path (string): Starting directory
          pattern (string): Search pattern
          excludePatterns (string[]): Exclude any patterns. Glob formats are supported.
      Case-insensitive matching
      Returns full paths to matches

- grep_files
      Search for text in files
      Inputs:
          path (string): Directory to search
          pattern (string): Text pattern to match
          excludePatterns (string[]): Exclude any patterns. Glob formats are supported.
      Returns:
          List of files containing the pattern with line numbers and the matched line content

- get_file_info
      Get detailed file/directory metadata
      Input: path (string)
      Returns:
          Size
          Creation time
          Modified time
          Access time
          Type (file/directory)
          Permissions

- list_allowed_directories
      List all directories the server is allowed to access
      No input required
      Returns:
          Directories that this server can read/write from

All of what follows will be part of the specification that will be generated, and this information does not need to be refined further at this time.

Technology stack:
- Python 3.12 virtual environment for dependencies
- FastMCP 2.0, https://gofastmcp.com

Implementation details:
- YAML file for configuration, such as the list of directories that the server is
allowed access to.
- run.sh script for quick start local development
