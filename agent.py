#!/usr/bin/env python3
"""
Agent CLI - Answers questions using LLM with tools.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON with 'answer', 'source', and 'tool_calls' fields to stdout.
    All debug output goes to stderr.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


# Constants
MAX_TOOL_CALLS = 15
PROJECT_ROOT = Path(__file__).parent


def load_env():
    """Load environment variables from .env.agent.secret and .env.docker.secret."""
    agent_env_file = Path(__file__).parent / ".env.agent.secret"
    docker_env_file = Path(__file__).parent / ".env.docker.secret"

    # Load agent environment (required)
    if agent_env_file.exists():
        load_dotenv(agent_env_file)
    else:
        print(f"Error: {agent_env_file} not found", file=sys.stderr)
        print(
            "Copy .env.agent.example to .env.agent.secret and configure it",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load docker environment (optional, for LMS_API_KEY)
    if docker_env_file.exists():
        load_dotenv(docker_env_file, override=False)


def get_llm_config() -> tuple[str, str, str]:
    """Get LLM configuration from environment variables."""
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL")

    if not api_key:
        print("Error: LLM_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not api_base:
        print("Error: LLM_API_BASE not set", file=sys.stderr)
        sys.exit(1)
    if not model:
        print("Error: LLM_MODEL not set", file=sys.stderr)
        sys.exit(1)

    return api_key, api_base, model


def validate_path(path: str) -> Path:
    """Validate and resolve a path, preventing directory traversal."""
    if ".." in path or path.startswith("/"):
        raise ValueError(f"Invalid path: {path}")

    full_path = (PROJECT_ROOT / path).resolve()

    if not str(full_path).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Path traversal detected: {path}")

    return full_path


def tool_read_file(path: str) -> str:
    """Read a file from the project repository.

    Args:
        path: Relative path from project root.

    Returns:
        File contents as string, or error message.
    """
    try:
        validated_path = validate_path(path)
        if not validated_path.exists():
            return f"Error: File not found: {path}"
        if not validated_path.is_file():
            return f"Error: Not a file: {path}"
        content = validated_path.read_text(encoding="utf-8")
        print(f"  Read file: {path} ({len(content)} chars)", file=sys.stderr)
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


def tool_list_files(path: str) -> str:
    """List files and directories at a given path.

    Args:
        path: Relative directory path from project root.

    Returns:
        Newline-separated listing, or error message.
    """
    try:
        validated_path = validate_path(path)
        if not validated_path.exists():
            return f"Error: Directory not found: {path}"
        if not validated_path.is_dir():
            return f"Error: Not a directory: {path}"

        entries = sorted(os.listdir(validated_path))
        result = "\n".join(entries)
        print(f"  Listed directory: {path} ({len(entries)} entries)", file=sys.stderr)
        return result
    except Exception as e:
        return f"Error listing {path}: {e}"


def tool_query_api(
    method: str, path: str, body: str | None = None, auth: bool = False
) -> str:
    """Call the backend API.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., '/items/', '/analytics/completion-rate')
        body: Optional JSON request body for POST/PUT requests
        auth: Whether to include authentication header (default: False)

    Returns:
        JSON string with status_code and body, or error message.
    """
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    api_key = os.getenv("LMS_API_KEY")

    url = f"{base_url}{path}"
    headers = {}

    if auth:
        if not api_key:
            return "Error: LMS_API_KEY not set in environment"
        headers["Authorization"] = f"Bearer {api_key}"

    print(f"  Calling API: {method} {url} (auth={auth})", file=sys.stderr)

    try:
        if body:
            headers["Content-Type"] = "application/json"
            response = httpx.request(
                method, url, headers=headers, content=body, timeout=30.0
            )
        else:
            response = httpx.request(method, url, headers=headers, timeout=30.0)

        result = {
            "status_code": response.status_code,
            "body": response.json() if response.content else response.text,
        }
        return json.dumps(result)
    except httpx.TimeoutException:
        return "Error: API request timed out (30s)"
    except httpx.HTTPError as e:
        return f"Error: HTTP error calling API: {e}"
    except Exception as e:
        return f"Error: Unexpected error calling API: {e}"


# Tool definitions for LLM function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository. Use this to read documentation, source code, or configuration files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md' or 'backend/app/main.py')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a directory. Use this to discover what files exist in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki' or 'backend')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the backend API to query data or test endpoints. Use this for questions about the running system, database counts, or API behavior. IMPORTANT: Set auth=false when testing unauthenticated requests (e.g., 'without authentication header', 'without sending credentials').",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                    },
                    "path": {
                        "type": "string",
                        "description": "API path (e.g., '/items/', '/analytics/completion-rate')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST/PUT requests",
                    },
                    "auth": {
                        "type": "boolean",
                        "description": "Whether to include authentication header (default: false). Set to true for authenticated requests.",
                        "default": False,
                    },
                },
                "required": ["method", "path"],
            },
        },
    },
]

# Map tool names to implementations
TOOL_IMPLEMENTATIONS = {
    "read_file": tool_read_file,
    "list_files": tool_list_files,
    "query_api": tool_query_api,
}

SYSTEM_PROMPT = """You are a helpful assistant that answers questions using the project wiki, source code, and backend API.

You have access to these tools:
- list_files(path): List files and directories in a directory
- read_file(path): Read the contents of a file
- query_api(method, path, body, auth): Call the backend API to query data or test endpoints

Strategy:
1. Use list_files("wiki") to discover documentation files
2. Use read_file() to read relevant files and find the answer
3. Use query_api() for questions about the running system, database counts, or API behavior
4. Include the source file path in your answer (e.g., wiki/git-workflow.md#section-name)
5. You can also read source code files (e.g., backend/app/main.py)

When to use each tool:
- Use query_api for data queries, API behavior, or status codes (unauthenticated by default)
- Use query_api with auth=true for endpoints requiring authentication
- Use read_file/list_files when asked about documentation, source code, or configuration

Rules:
- ALWAYS include the source file path in your final answer (e.g., "Source: wiki/file.md#section")
- Use markdown anchors for sections when possible (e.g., wiki/file.md#section-name)
- Make at most 15 tool calls
- COMPLETELY explore directories before answering - don't stop midway
- When you find relevant files, READ them with read_file before answering
- Give a COMPLETE answer before stopping - don't say "let me check" without actually checking
- NEVER say "let me examine" or "let me check" - actually DO the examination with tools
- When you have the answer, return it immediately without more tool calls
- If a file doesn't exist or can't be read, try a different approach
- If an API call fails, try to understand the error and explain it
"""


def call_llm(
    messages: list[dict[str, Any]],
    api_key: str,
    api_base: str,
    model: str,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Call the LLM API and return the response.

    Args:
        messages: List of message dicts with 'role' and 'content'
        api_key: API key for authentication
        api_base: Base URL of the API
        model: Model name to use
        tools: Optional list of tool definitions for function calling

    Returns:
        The LLM response dict
    """
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
    }
    if tools:
        body["tools"] = tools

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()


def execute_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Execute a single tool call and return the result.

    Args:
        tool_call: Tool call dict from LLM response

    Returns:
        Result dict with tool name, args, and result
    """
    function = tool_call.get("function", {})
    tool_name = function.get("name")
    args_str = function.get("arguments", "{}")

    try:
        args = json.loads(args_str)
    except json.JSONDecodeError:
        args = {}

    print(f"  Calling tool: {tool_name}({args})", file=sys.stderr)

    if tool_name not in TOOL_IMPLEMENTATIONS:
        result = f"Error: Unknown tool: {tool_name}"
    else:
        tool_func = TOOL_IMPLEMENTATIONS[tool_name]
        try:
            result = tool_func(**args)
        except Exception as e:
            result = f"Error: {e}"

    return {
        "tool": tool_name,
        "args": args,
        "result": result,
    }


def run_agentic_loop(
    question: str,
    api_key: str,
    api_base: str,
    model: str,
) -> tuple[str, str, list[dict[str, Any]]]:
    """Run the agentic loop to answer a question.

    Args:
        question: User's question
        api_key: API key for authentication
        api_base: Base URL of the API
        model: Model name to use

    Returns:
        Tuple of (answer, source, tool_calls)
    """
    # Initialize conversation with system prompt
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    all_tool_calls = []
    iteration = 0

    while iteration < MAX_TOOL_CALLS:
        iteration += 1
        print(f"Iteration {iteration}...", file=sys.stderr)

        # Call LLM with tools
        response = call_llm(messages, api_key, api_base, model, tools=TOOLS)

        # Get the assistant message
        choices = response.get("choices", [])
        if not choices:
            print("Error: No choices in LLM response", file=sys.stderr)
            return "Error: No response from LLM", "", all_tool_calls

        message = choices[0].get("message", {})
        content = message.get("content")
        tool_calls = message.get("tool_calls", [])

        # If no tool calls, we have the final answer
        if not tool_calls:
            print(f"  Final answer received", file=sys.stderr)
            # Extract source from content if possible
            source = extract_source(content or "")
            return content or "", source, all_tool_calls

        # Add assistant message with tool calls to conversation
        # Handle case where content might be null
        assistant_message = {"role": "assistant"}
        if content:
            assistant_message["content"] = content
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls

        messages.append(assistant_message)

        # Execute tool calls
        for tool_call in tool_calls:
            result = execute_tool_call(tool_call)
            all_tool_calls.append(result)

            # Add tool response to messages
            # OpenAI format: role=tool, tool_call_id=string, content=string
            tool_call_id = tool_call.get("id", "")
            if not tool_call_id:
                # Generate a simple ID if not provided
                tool_call_id = f"call_{len(all_tool_calls)}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result["result"],
                }
            )

    # Max iterations reached
    print("Max tool calls reached", file=sys.stderr)
    return "Max tool calls reached", "", all_tool_calls


def extract_source(content: str) -> str:
    """Extract source reference from content if present."""
    import re

    # Look for patterns like wiki/file.md or wiki/file.md#section
    match = re.search(r"(wiki/[\w\-/]+\.md(?:#[\w\-]+)?)", content)
    if match:
        return match.group(1)

    # Look for patterns like (file.md#section) in parentheses
    match = re.search(r"\(([\w\-/]+\.md(?:#[\w\-]+)?)\)", content)
    if match:
        filename = match.group(1)
        if filename.startswith("wiki/"):
            return filename
        return f"wiki/{filename}"

    # Look for patterns like "in the xxx.md file" or "from xxx.md"
    match = re.search(r"(?:in|from|see) the ([\w\-/]+\.md)", content, re.IGNORECASE)
    if match:
        filename = match.group(1)
        # If it's already a full path like wiki/github.md
        if filename.startswith("wiki/"):
            # Try to find a section heading mentioned
            section_match = re.search(r"##?\s+([A-Za-z\s]+?)(?:\.|$)", content)
            if section_match:
                section = section_match.group(1).strip().lower().replace(" ", "-")
                return f"{filename}#{section}"
            return filename
        # Otherwise assume it's in wiki/
        return f"wiki/{filename}"

    # Look for Source: xxx pattern
    match = re.search(r"Source:\s*([\w\-/]+\.md(?:#[\w\-]+)?)", content, re.IGNORECASE)
    if match:
        return match.group(1)

    return ""


def main():
    """Main entry point."""
    # Check command-line arguments
    if len(sys.argv) < 2:
        print('Usage: uv run agent.py "Your question here"', file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    # Load configuration
    load_env()
    api_key, api_base, model = get_llm_config()

    print(f"Question: {question}", file=sys.stderr)
    print(f"Model: {model}", file=sys.stderr)

    # Run agentic loop
    answer, source, tool_calls = run_agentic_loop(question, api_key, api_base, model)

    # Output JSON result
    result = {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls,
    }

    # Only valid JSON to stdout
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
