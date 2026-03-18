# Task 2 Plan: The Documentation Agent

## Overview

Task 2 extends the Task 1 agent with tools (`read_file`, `list_files`) and an agentic loop. The agent can now navigate the project wiki, read files, and answer questions with source references.

## Agentic Loop Architecture

### Flow

```
User Question
    │
    ▼
┌─────────────────────────────────┐
│  Send question + tool defs to   │
│  LLM with system prompt         │
└────────────┬────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ LLM responds │
      └──────┬───────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
Tool calls?      No tool calls
    │                 │
    │ Yes             │
    │                 ▼
    │          Final answer → Output JSON
    ▼
Execute tools
    │
    ▼
Append results as
tool role messages
    │
    ▼
Loop back to LLM
(max 10 iterations)
```

### Implementation Steps

1. **Send to LLM:** User question + tool definitions in system prompt
2. **Parse Response:** Check for `tool_calls` in LLM response
3. **Execute Tools:** If tool calls present, execute each tool
4. **Feed Back:** Append tool results as `tool` role messages
5. **Repeat:** Go back to step 1 until LLM gives final answer
6. **Output:** Format JSON with `answer`, `source`, and `tool_calls`

## Tool Definitions

### `read_file`

**Purpose:** Read a file from the project repository.

**Schema:**
```python
{
    "name": "read_file",
    "description": "Read a file from the project repository",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
            }
        },
        "required": ["path"]
    }
}
```

**Implementation:**
- Open file at `Path(project_root) / path`
- Return contents as string
- Error handling: file not found, permission denied
- Security: reject paths with `../` traversal

### `list_files`

**Purpose:** List files and directories at a given path.

**Schema:**
```python
{
    "name": "list_files",
    "description": "List files and directories in a directory",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative directory path from project root (e.g., 'wiki')"
            }
        },
        "required": ["path"]
    }
}
```

**Implementation:**
- List directory at `Path(project_root) / path`
- Return newline-separated listing
- Error handling: directory not found, not a directory
- Security: reject paths with `../` traversal

## Path Security

Both tools must prevent directory traversal attacks:

```python
def validate_path(path: str) -> Path:
    """Validate and resolve a path, preventing traversal."""
    # Reject obvious traversal attempts
    if ".." in path or path.startswith("/"):
        raise ValueError(f"Invalid path: {path}")
    
    # Resolve to absolute path
    project_root = Path(__file__).parent
    full_path = (project_root / path).resolve()
    
    # Ensure path is within project root
    if not str(full_path).startswith(str(project_root)):
        raise ValueError(f"Path traversal detected: {path}")
    
    return full_path
```

## System Prompt Strategy

The system prompt guides the LLM to:

1. Use `list_files` to discover wiki files
2. Use `read_file` to find specific information
3. Include source references (file path + section anchor)
4. Stop after finding the answer (max 10 tool calls)

**Example System Prompt:**
```
You are a helpful assistant that answers questions using the project wiki.

You have access to these tools:
- list_files(path): List files in a directory
- read_file(path): Read a file's contents

Strategy:
1. Use list_files("wiki") to discover documentation files
2. Use read_file() to read relevant files
3. Find the answer and cite the source (file path + section)
4. Return the final answer with the source

Rules:
- Always include the source file path
- Use markdown anchors for sections (e.g., wiki/file.md#section-name)
- Make at most 10 tool calls
- When you have the answer, return it immediately
```

## Output Format

```json
{
  "answer": "The answer text",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "..."
    }
  ]
}
```

**Fields:**
- `answer` (string, required): The final answer
- `source` (string, required): Wiki section reference
- `tool_calls` (array, required): All tool calls made during the loop

## Testing Strategy

Add 2 regression tests:

1. **Test: Merge conflict question**
   - Question: "How do you resolve a merge conflict?"
   - Expected: `read_file` in tool_calls, `wiki/git-workflow.md` in source

2. **Test: Wiki listing question**
   - Question: "What files are in the wiki?"
   - Expected: `list_files` in tool_calls

## Files to Update/Create

1. `plans/task-2.md` - This plan
2. `agent.py` - Add tools and agentic loop
3. `AGENT.md` - Document tools and loop
4. `tests/test_agent.py` - Add 2 more tests

## Acceptance Criteria Checklist

- [ ] Plan committed before code
- [ ] `agent.py` defines `read_file` and `list_files` as tool schemas
- [ ] Agentic loop executes tool calls and feeds results back
- [ ] `tool_calls` in output is populated when tools are used
- [ ] `source` field correctly identifies wiki section
- [ ] Tools do not access files outside project directory
- [ ] `AGENT.md` documents tools and agentic loop
- [ ] 2 tool-calling regression tests exist and pass
