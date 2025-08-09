# ABOUT-ME: Tests for MCP tool handlers functionality
# ABOUT-ME: Tests file operations like list_directory, create_file, etc.

import pytest
import asyncio
import json
import os
import tempfile
from src.server import mcp

@pytest.mark.asyncio
async def test_list_directory_tool():
    """Test that list_directory tool returns file and directory information"""
    # Create a temporary directory with some test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files and directories
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        test_subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(test_subdir)
        
        # Call the list_directory tool
        result = await mcp.call_tool("list_directory", {"path": temp_dir})
        
        # FastMCP returns a list of TextContent objects
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Expect a list of files/directories with metadata
        assert isinstance(response_data, list)
        assert len(response_data) >= 2  # At least test.txt and subdir
        
        # Check that each item has expected fields
        for item in response_data:
            assert "name" in item
            assert "type" in item  # 'file' or 'directory'
            assert "size" in item
            assert "modified" in item
            assert "permissions" in item
        
        # Verify our test files are in the response
        names = [item["name"] for item in response_data]
        assert "test.txt" in names
        assert "subdir" in names
        
        # Verify file vs directory types
        for item in response_data:
            if item["name"] == "test.txt":
                assert item["type"] == "file"
                assert item["size"] > 0
            elif item["name"] == "subdir":
                assert item["type"] == "directory"

@pytest.mark.asyncio
async def test_list_directory_tool_registered():
    """Test that list_directory tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "list_directory" in tool_names

@pytest.mark.asyncio 
async def test_list_directory_nonexistent_path():
    """Test that list_directory handles nonexistent paths gracefully"""
    # Try to list a nonexistent directory
    with pytest.raises(Exception):  # Should raise an error for invalid path
        await mcp.call_tool("list_directory", {"path": "/nonexistent/path"})

@pytest.mark.asyncio
async def test_create_directory_tool():
    """Test that create_directory tool creates directories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Path for new directory to create
        new_dir_path = os.path.join(temp_dir, "new_directory")
        
        # Verify directory doesn't exist initially
        assert not os.path.exists(new_dir_path)
        
        # Call the create_directory tool
        result = await mcp.call_tool("create_directory", {"path": new_dir_path})
        
        # FastMCP returns a list of TextContent objects
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Expect success response
        assert "success" in response_data
        assert response_data["success"] is True
        assert "path" in response_data
        assert response_data["path"] == new_dir_path
        
        # Verify directory was actually created
        assert os.path.exists(new_dir_path)
        assert os.path.isdir(new_dir_path)

@pytest.mark.asyncio
async def test_create_directory_nested_path():
    """Test that create_directory can create nested directories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Path for nested directory to create
        nested_path = os.path.join(temp_dir, "level1", "level2", "level3")
        
        # Verify nested path doesn't exist initially
        assert not os.path.exists(nested_path)
        
        # Call the create_directory tool
        result = await mcp.call_tool("create_directory", {"path": nested_path})
        
        # Parse response
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        
        # Verify nested directory was created
        assert os.path.exists(nested_path)
        assert os.path.isdir(nested_path)

@pytest.mark.asyncio
async def test_create_directory_already_exists():
    """Test that create_directory handles existing directories gracefully"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Try to create a directory that already exists
        result = await mcp.call_tool("create_directory", {"path": temp_dir})
        
        # Should succeed (idempotent operation)
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True

@pytest.mark.asyncio
async def test_create_directory_tool_registered():
    """Test that create_directory tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "create_directory" in tool_names

@pytest.mark.asyncio
async def test_create_file_tool():
    """Test that create_file tool creates files with content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Path for new file to create
        new_file_path = os.path.join(temp_dir, "test_file.txt")
        test_content = "Hello, World!\nThis is test content."
        
        # Verify file doesn't exist initially
        assert not os.path.exists(new_file_path)
        
        # Call the create_file tool
        result = await mcp.call_tool("create_file", {
            "path": new_file_path,
            "content": test_content
        })
        
        # FastMCP returns a list of TextContent objects
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Expect success response
        assert "success" in response_data
        assert response_data["success"] is True
        assert "path" in response_data
        assert response_data["path"] == new_file_path
        assert "size" in response_data
        
        # Verify file was actually created with correct content
        assert os.path.exists(new_file_path)
        assert os.path.isfile(new_file_path)
        
        with open(new_file_path, "r") as f:
            created_content = f.read()
        assert created_content == test_content
        
        # Verify size matches
        assert response_data["size"] == len(test_content)

@pytest.mark.asyncio
async def test_create_file_overwrite():
    """Test that create_file can overwrite existing files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "existing_file.txt")
        
        # Create initial file
        initial_content = "Initial content"
        with open(file_path, "w") as f:
            f.write(initial_content)
        
        # Overwrite with new content
        new_content = "New content that replaces the old"
        result = await mcp.call_tool("create_file", {
            "path": file_path,
            "content": new_content
        })
        
        # Parse response
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        
        # Verify content was replaced
        with open(file_path, "r") as f:
            final_content = f.read()
        assert final_content == new_content

@pytest.mark.asyncio
async def test_create_file_empty():
    """Test that create_file can create empty files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        empty_file_path = os.path.join(temp_dir, "empty.txt")
        
        # Create empty file
        result = await mcp.call_tool("create_file", {
            "path": empty_file_path,
            "content": ""
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["size"] == 0
        
        # Verify empty file exists
        assert os.path.exists(empty_file_path)
        assert os.path.getsize(empty_file_path) == 0

@pytest.mark.asyncio
async def test_create_file_tool_registered():
    """Test that create_file tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "create_file" in tool_names

@pytest.mark.asyncio
async def test_append_file_tool():
    """Test that append_file tool appends content to existing files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial file with content
        file_path = os.path.join(temp_dir, "append_test.txt")
        initial_content = "Initial line\n"
        with open(file_path, "w") as f:
            f.write(initial_content)
        
        # Content to append
        append_content = "Appended line\nAnother appended line\n"
        
        # Call the append_file tool
        result = await mcp.call_tool("append_file", {
            "path": file_path,
            "content": append_content
        })
        
        # FastMCP returns a list of TextContent objects
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Expect success response
        assert "success" in response_data
        assert response_data["success"] is True
        assert "path" in response_data
        assert response_data["path"] == file_path
        assert "size" in response_data
        
        # Verify content was appended correctly
        with open(file_path, "r") as f:
            final_content = f.read()
        
        expected_content = initial_content + append_content
        assert final_content == expected_content
        
        # Verify size matches
        assert response_data["size"] == len(expected_content)

@pytest.mark.asyncio
async def test_append_file_new_file():
    """Test that append_file creates new file if it doesn't exist"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Path for new file
        new_file_path = os.path.join(temp_dir, "new_append_file.txt")
        content_to_append = "This is new content\n"
        
        # Verify file doesn't exist initially
        assert not os.path.exists(new_file_path)
        
        # Call append_file on non-existent file
        result = await mcp.call_tool("append_file", {
            "path": new_file_path,
            "content": content_to_append
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        
        # Verify file was created with content
        assert os.path.exists(new_file_path)
        with open(new_file_path, "r") as f:
            file_content = f.read()
        assert file_content == content_to_append

@pytest.mark.asyncio
async def test_append_file_empty_content():
    """Test that append_file handles empty content gracefully"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "empty_append.txt")
        initial_content = "Original content"
        
        # Create initial file
        with open(file_path, "w") as f:
            f.write(initial_content)
        
        # Append empty content
        result = await mcp.call_tool("append_file", {
            "path": file_path,
            "content": ""
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        
        # Verify content unchanged
        with open(file_path, "r") as f:
            final_content = f.read()
        assert final_content == initial_content

@pytest.mark.asyncio
async def test_append_file_tool_registered():
    """Test that append_file tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "append_file" in tool_names

@pytest.mark.asyncio
async def test_read_text_file_tool():
    """Test that read_text_file tool reads file content correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file with content
        file_path = os.path.join(temp_dir, "read_test.txt")
        test_content = "Line 1\nLine 2\nLine 3 with special chars: äöü\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Call the read_text_file tool
        result = await mcp.call_tool("read_text_file", {"path": file_path})
        
        # FastMCP returns a list of TextContent objects
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Expect success response with content
        assert "success" in response_data
        assert response_data["success"] is True
        assert "path" in response_data
        assert response_data["path"] == file_path
        assert "content" in response_data
        assert "size" in response_data
        
        # Verify content matches
        assert response_data["content"] == test_content
        # Size should match actual file size (UTF-8 encoded bytes)
        expected_size = len(test_content.encode('utf-8'))
        assert response_data["size"] == expected_size

@pytest.mark.asyncio
async def test_read_text_file_empty():
    """Test that read_text_file handles empty files correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create empty file
        empty_file_path = os.path.join(temp_dir, "empty.txt")
        with open(empty_file_path, "w") as f:
            pass  # Create empty file
        
        # Read empty file
        result = await mcp.call_tool("read_text_file", {"path": empty_file_path})
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["content"] == ""
        assert response_data["size"] == 0

@pytest.mark.asyncio
async def test_read_text_file_nonexistent():
    """Test that read_text_file handles nonexistent files gracefully"""
    # Try to read a nonexistent file
    with pytest.raises(Exception):  # Should raise an error for missing file
        await mcp.call_tool("read_text_file", {"path": "/nonexistent/file.txt"})

@pytest.mark.asyncio
async def test_read_text_file_large():
    """Test that read_text_file handles reasonably large files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file with multiple lines
        large_file_path = os.path.join(temp_dir, "large.txt")
        lines = [f"Line {i}: This is line number {i}\n" for i in range(100)]
        large_content = "".join(lines)
        
        with open(large_file_path, "w") as f:
            f.write(large_content)
        
        # Read large file
        result = await mcp.call_tool("read_text_file", {"path": large_file_path})
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["content"] == large_content
        assert response_data["size"] == len(large_content)

@pytest.mark.asyncio
async def test_read_text_file_tool_registered():
    """Test that read_text_file tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "read_text_file" in tool_names

def test_handlers_placeholder():
    """Placeholder test for handlers"""
    assert True

# Find Files Tests
@pytest.mark.asyncio
async def test_find_files_by_name():
    """Test finding files by name pattern"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test1_path = os.path.join(temp_dir, "test1.txt")
        test2_path = os.path.join(temp_dir, "test2.txt")
        other_path = os.path.join(temp_dir, "other.log")
        
        with open(test1_path, "w") as f:
            f.write("content1")
        with open(test2_path, "w") as f:
            f.write("content2")
        with open(other_path, "w") as f:
            f.write("log content")
        
        result = await mcp.call_tool("find_files", {
            "path": temp_dir,
            "pattern": "*.txt"
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["files"]) == 2
        file_names = [f["name"] for f in response_data["files"]]
        assert "test1.txt" in file_names
        assert "test2.txt" in file_names

@pytest.mark.asyncio
async def test_find_files_recursive():
    """Test finding files recursively in subdirectories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested structure
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        
        root_file = os.path.join(temp_dir, "root.txt")
        nested_file = os.path.join(subdir, "nested.txt")
        
        with open(root_file, "w") as f:
            f.write("root content")
        with open(nested_file, "w") as f:
            f.write("nested content")
        
        result = await mcp.call_tool("find_files", {
            "path": temp_dir,
            "pattern": "*.txt",
            "recursive": True
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["files"]) == 2
        file_names = [f["name"] for f in response_data["files"]]
        assert "root.txt" in file_names
        assert "nested.txt" in file_names

@pytest.mark.asyncio
async def test_find_files_nonexistent_path():
    """Test finding files in non-existent path"""
    with pytest.raises(Exception):  # Should raise an error for non-existent directory
        await mcp.call_tool("find_files", {
            "path": "/nonexistent/path",
            "pattern": "*"
        })

@pytest.mark.asyncio
async def test_find_files_outside_allowed_dirs():
    """Test finding files outside allowed directories"""
    with pytest.raises(Exception):  # Should raise an error for access denied
        await mcp.call_tool("find_files", {
            "path": "/etc",
            "pattern": "*"
        })

@pytest.mark.asyncio
async def test_find_files_empty_result():
    """Test finding files with pattern that matches nothing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("content")
        
        result = await mcp.call_tool("find_files", {
            "path": temp_dir,
            "pattern": "*.nonexistent"
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["files"]) == 0

@pytest.mark.asyncio
async def test_find_files_tool_registered():
    """Test that find_files tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "find_files" in tool_names

# Grep Files Tests
@pytest.mark.asyncio
async def test_grep_files_basic_search():
    """Test basic text search in files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with content
        file1_path = os.path.join(temp_dir, "file1.txt")
        file2_path = os.path.join(temp_dir, "file2.txt")
        file3_path = os.path.join(temp_dir, "file3.log")
        
        with open(file1_path, "w") as f:
            f.write("Hello world\nThis is a test\nAnother line")
        with open(file2_path, "w") as f:
            f.write("Hello again\nNo match here\nEnd of file")
        with open(file3_path, "w") as f:
            f.write("Log entry: Hello\nError occurred\nDebug info")
        
        result = await mcp.call_tool("grep_files", {
            "path": temp_dir,
            "pattern": "Hello",
            "file_pattern": "*"
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["matches"]) >= 2  # Should find matches in file1 and file3
        
        # Check that matches contain file paths and line information
        match_files = [match["file"] for match in response_data["matches"]]
        assert any("file1.txt" in f for f in match_files)
        assert any("file3.log" in f for f in match_files)

@pytest.mark.asyncio
async def test_grep_files_regex_search():
    """Test regex pattern search in files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file with various patterns
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Email: user@example.com\nPhone: 123-456-7890\nInvalid: not-an-email")
        
        result = await mcp.call_tool("grep_files", {
            "path": temp_dir,
            "pattern": r"\w+@\w+\.\w+",  # Email regex
            "file_pattern": "*.txt",
            "regex": True
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["matches"]) == 1
        assert "user@example.com" in response_data["matches"][0]["line"]

@pytest.mark.asyncio
async def test_grep_files_recursive():
    """Test recursive search in subdirectories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested structure
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        
        root_file = os.path.join(temp_dir, "root.txt")
        nested_file = os.path.join(subdir, "nested.txt")
        
        with open(root_file, "w") as f:
            f.write("TARGET found in root")
        with open(nested_file, "w") as f:
            f.write("TARGET found in nested directory")
        
        result = await mcp.call_tool("grep_files", {
            "path": temp_dir,
            "pattern": "TARGET",
            "file_pattern": "*.txt",
            "recursive": True
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["matches"]) == 2
        match_files = [match["file"] for match in response_data["matches"]]
        assert any("root.txt" in f for f in match_files)
        assert any("nested.txt" in f for f in match_files)

@pytest.mark.asyncio
async def test_grep_files_case_insensitive():
    """Test case-insensitive search"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello World\nhello world\nHELLO WORLD")
        
        result = await mcp.call_tool("grep_files", {
            "path": temp_dir,
            "pattern": "hello",
            "file_pattern": "*.txt",
            "case_sensitive": False
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["matches"]) == 3  # Should find all three variations

@pytest.mark.asyncio
async def test_grep_files_nonexistent_path():
    """Test grep search in non-existent path"""
    with pytest.raises(Exception):  # Should raise an error for non-existent directory
        await mcp.call_tool("grep_files", {
            "path": "/nonexistent/path",
            "pattern": "test",
            "file_pattern": "*"
        })

@pytest.mark.asyncio
async def test_grep_files_outside_allowed_dirs():
    """Test grep search outside allowed directories"""
    with pytest.raises(Exception):  # Should raise an error for access denied
        await mcp.call_tool("grep_files", {
            "path": "/etc",
            "pattern": "test",
            "file_pattern": "*"
        })

@pytest.mark.asyncio
async def test_grep_files_no_matches():
    """Test grep search with no matches"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("This file contains no target text")
        
        result = await mcp.call_tool("grep_files", {
            "path": temp_dir,
            "pattern": "NONEXISTENT",
            "file_pattern": "*.txt"
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["matches"]) == 0

@pytest.mark.asyncio
async def test_grep_files_tool_registered():
    """Test that grep_files tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "grep_files" in tool_names

# Get File Info Tests
@pytest.mark.asyncio
async def test_get_file_info_basic():
    """Test getting file information for a regular file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = "Hello, world!\nThis is a test file."
        
        with open(test_file, "w") as f:
            f.write(test_content)
        
        result = await mcp.call_tool("get_file_info", {
            "path": test_file
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["path"] == test_file
        assert response_data["type"] == "file"
        assert response_data["size"] == len(test_content)
        assert "modified" in response_data
        assert "permissions" in response_data
        assert response_data["exists"] is True

@pytest.mark.asyncio
async def test_get_file_info_directory():
    """Test getting file information for a directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = await mcp.call_tool("get_file_info", {
            "path": temp_dir
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["path"] == temp_dir
        assert response_data["type"] == "directory"
        assert "modified" in response_data
        assert "permissions" in response_data
        assert response_data["exists"] is True

@pytest.mark.asyncio
async def test_get_file_info_nonexistent():
    """Test getting file information for non-existent file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        nonexistent_path = os.path.join(temp_dir, "nonexistent.txt")
        
        result = await mcp.call_tool("get_file_info", {
            "path": nonexistent_path
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["path"] == nonexistent_path
        assert response_data["exists"] is False
        assert response_data["type"] is None

@pytest.mark.asyncio
async def test_get_file_info_outside_allowed_dirs():
    """Test getting file info outside allowed directories"""
    with pytest.raises(Exception):  # Should raise an error for access denied
        await mcp.call_tool("get_file_info", {
            "path": "/etc/passwd"
        })

@pytest.mark.asyncio
async def test_get_file_info_with_detailed_permissions():
    """Test getting detailed file information including permissions"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "permissions_test.txt")
        
        with open(test_file, "w") as f:
            f.write("test content")
        
        # Set specific permissions
        os.chmod(test_file, 0o644)
        
        result = await mcp.call_tool("get_file_info", {
            "path": test_file,
            "detailed": True
        })
        
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert "readable" in response_data
        assert "writable" in response_data
        assert "executable" in response_data
        assert response_data["readable"] is True
        assert response_data["writable"] is True

@pytest.mark.asyncio
async def test_get_file_info_tool_registered():
    """Test that get_file_info tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "get_file_info" in tool_names

# List Allowed Directories Tests
@pytest.mark.asyncio
async def test_list_allowed_directories():
    """Test listing allowed directories from configuration"""
    result = await mcp.call_tool("list_allowed_directories", {})
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "directories" in response_data
    assert isinstance(response_data["directories"], list)
    assert len(response_data["directories"]) > 0
    
    # Check that directories contain expected structure
    for directory in response_data["directories"]:
        assert "path" in directory
        assert "exists" in directory
        assert "readable" in directory

@pytest.mark.asyncio
async def test_list_allowed_directories_with_details():
    """Test listing allowed directories with detailed information"""
    result = await mcp.call_tool("list_allowed_directories", {
        "detailed": True
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "directories" in response_data
    
    # Check detailed information is included
    for directory in response_data["directories"]:
        assert "path" in directory
        assert "exists" in directory
        assert "readable" in directory
        if directory["exists"]:
            assert "size" in directory or "type" in directory

@pytest.mark.asyncio
async def test_list_allowed_directories_tool_registered():
    """Test that list_allowed_directories tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "list_allowed_directories" in tool_names

# Get User Usage Stats Tests
@pytest.mark.asyncio
async def test_get_user_usage_stats():
    """Test getting usage statistics for a specific user"""
    result = await mcp.call_tool("get_user_usage_stats", {
        "username": "testuser"
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "username" in response_data
    assert "usage" in response_data
    assert response_data["username"] == "testuser"
    assert isinstance(response_data["usage"], dict)

@pytest.mark.asyncio
async def test_get_user_usage_stats_with_dates():
    """Test getting user usage stats with date filtering"""
    result = await mcp.call_tool("get_user_usage_stats", {
        "username": "testuser",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "username" in response_data
    assert "usage" in response_data
    assert "start_date" in response_data
    assert "end_date" in response_data

@pytest.mark.asyncio
async def test_get_user_usage_stats_nonexistent_user():
    """Test getting usage stats for non-existent user"""
    result = await mcp.call_tool("get_user_usage_stats", {
        "username": "nonexistentuser"
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert response_data["username"] == "nonexistentuser"
    # Should return empty or zero usage for non-existent user

@pytest.mark.asyncio
async def test_get_user_usage_stats_tool_registered():
    """Test that get_user_usage_stats tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "get_user_usage_stats" in tool_names

# Get Usage Stats Tests
@pytest.mark.asyncio
async def test_get_usage_stats():
    """Test getting overall usage statistics"""
    result = await mcp.call_tool("get_usage_stats", {})
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "stats" in response_data
    assert isinstance(response_data["stats"], dict)
    assert "total_requests" in response_data["stats"]
    assert "unique_users" in response_data["stats"]

@pytest.mark.asyncio
async def test_get_usage_stats_with_dates():
    """Test getting usage stats with date filtering"""
    result = await mcp.call_tool("get_usage_stats", {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "stats" in response_data
    assert "start_date" in response_data
    assert "end_date" in response_data

@pytest.mark.asyncio
async def test_get_usage_stats_detailed():
    """Test getting detailed usage statistics"""
    result = await mcp.call_tool("get_usage_stats", {
        "detailed": True
    })
    
    response_data = json.loads(result[0].text)
    assert response_data["success"] is True
    assert "stats" in response_data
    assert "user_breakdown" in response_data["stats"]

@pytest.mark.asyncio
async def test_get_usage_stats_tool_registered():
    """Test that get_usage_stats tool is properly registered"""
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "get_usage_stats" in tool_names
