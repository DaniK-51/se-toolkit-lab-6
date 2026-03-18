# Agent Architecture

## Overview

This agent is a CLI tool that answers questions by calling an LLM with access to tools. It implements a full agentic loop that can:

1. **Call an LLM** (Task 1) - Basic question answering
2. **Read documentation** (Task 2) - Navigate wiki and source code using `read_file` and `list_files` tools
3. **Query the backend** (Task 3) - Access running API using `query_api` tool

## LLM Provider

**Provider:** Qwen Code API (self-hosted on VM)

**Why Qwen Code?**
- 1000 free requests per day
- Works from Russia without VPN
- No credit card required
- OpenAI-compatible API endpoint

**Model:** `qwen3-coder-plus`

**Configuration:**
- API Base: `http://<vm-ip>:42005/v1` (Qwen Code API proxy running on VM)
- API Key: Stored in `.env.agent.secret` as `LLM_API_KEY`
- Model: Specified in `.env.agent.secret` as `LLM_MODEL`

## Architecture

### Components

1. **Environment Loader** (`load_env()`)
   - Loads `.env.agent.secret` for LLM configuration
   - Loads `.env.docker.secret` for backend API key (`LMS_API_KEY`)
   - Uses `python-dotenv` to parse environment variables
   - Exits with error if required files are missing

2. **Configuration Manager** (`get_llm_config()`)
   - Reads `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` from environment
   - Validates all required variables are present
   - Returns configuration tuple

3. **LLM Client** (`call_llm()`)
   - Makes HTTP POST request to `{api_base}/chat/completions`
   - Uses `httpx` client with 60-second timeout
   - Supports tool/function calling via OpenAI-compatible API
   - Handles errors: timeout, HTTP errors, missing response fields

4. **Tool Implementations**
   - `read_file(path)`: Read a file from the project repository
   - `list_files(path)`: List files and directories at a given path
   - `query_api(method, path, body)`: Call the backend API with authentication

5. **Agentic Loop** (`run_agentic_loop()`)
   - Sends user question + tool definitions to LLM
   - Parses response for tool calls
   - Executes tools and feeds results back
   - Repeats until LLM provides final answer (max 10 iterations)
   - Returns answer, source, and tool call history

6. **CLI Interface** (`main()`)
   - Accepts question as first command-line argument
   - Orchestrates: load env → get config → run loop → output result
   - Outputs JSON to stdout, debug info to stderr

### Tools

#### `read_file`

Read a file from the project repository.

**Parameters:**
- `path` (string, required): Relative path from project root

**Returns:** File contents as string, or error message

**Security:** Validates path to prevent directory traversal (`../`)

#### `list_files`

List files and directories at a given path.

**Parameters:**
- `path` (string, required): Relative directory path from project root

**Returns:** Newline-separated listing, or error message

**Security:** Validates path to prevent directory traversal

#### `query_api`

Call the backend API to query data or test endpoints.

**Parameters:**
- `method` (string, required): HTTP method (GET, POST, etc.)
- `path` (string, required): API path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (string, optional): JSON request body for POST/PUT requests

**Returns:** JSON string with `status_code` and `body`, or error message

**Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret` with `Authorization: Bearer` header

### Data Flow

```
┌─────────────────┐
│ User Question   │ (CLI argument)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  load_env()     │ (.env.agent.secret, .env.docker.secret)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ get_llm_config()│ (LLM_API_KEY, BASE, MODEL)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  run_agentic_loop()             │
│  ┌───────────────────────────┐  │
│  │ Send to LLM with tools    │  │
│  └─────────────┬─────────────┘  │
│                │                 │
│         ┌──────┴──────┐         │
│         │             │         │
│         ▼             ▼         │
│    Tool calls?    No tools      │
│         │             │         │
│    Yes  │             │         │
│         │             ▼         │
│         │       Final answer    │
│         ▼             │         │
│   Execute tools       │         │
│         │             │         │
│         └──────┬──────┘         │
│                │                 │
│         Feed back to LLM        │
│                │                 │
│         (max 10 iterations)     │
└────────────────┼────────────────┘
                 │
                 ▼
┌─────────────────┐
│  Output JSON    │ {"answer": "...", "source": "...", "tool_calls": [...]}
└─────────────────┘
```

## Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "The LLM's response text",
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
- `answer` (string, required): The LLM's answer to the question
- `source` (string, required): Wiki section reference or empty for API queries
- `tool_calls` (array, required): All tool calls made during the agentic loop

**Error Handling:**
- All error messages go to stderr
- Exit code 0 on success, non-zero on error
- 60-second timeout on LLM requests
- 30-second timeout on API requests

## Environment Variables

| Variable             | Purpose                              | Source                    |
| -------------------- | ------------------------------------ | ------------------------- |
| `LLM_API_KEY`        | LLM provider API key                 | `.env.agent.secret`       |
| `LLM_API_BASE`       | LLM API endpoint URL                 | `.env.agent.secret`       |
| `LLM_MODEL`          | Model name                           | `.env.agent.secret`       |
| `LMS_API_KEY`        | Backend API key for `query_api` auth | `.env.docker.secret`      |
| `AGENT_API_BASE_URL` | Base URL for `query_api`             | Optional, defaults to `http://localhost:42002` |

## How to Run

```bash
# Basic usage
uv run agent.py "What is 2+2?"

# Documentation question (Task 2)
uv run agent.py "How do you resolve a merge conflict?"

# API question (Task 3)
uv run agent.py "How many items are in the database?"
```

## Testing

Run tests with:

```bash
uv run pytest tests/ -v
```

**Test Coverage:**
- Task 1: Basic LLM integration (JSON output, required fields)
- Task 2: Tool calling for documentation questions (`read_file`, `list_files`)
- Task 3: API querying for system questions (`query_api`)

## System Prompt Strategy

The system prompt guides the LLM to:

1. **Choose the right tool:**
   - Use `query_api` for data/API questions
   - Use `read_file`/`list_files` for documentation/code questions

2. **Navigate efficiently:**
   - Start with `list_files("wiki")` to discover docs
   - Read relevant files with `read_file`

3. **Cite sources:**
   - Include file path in answer
   - Use markdown anchors for sections

4. **Know when to stop:**
   - Return answer immediately when found
   - Maximum 10 tool calls

## Benchmark Evaluation

Run the local benchmark:

```bash
uv run run_eval.py
```

The benchmark tests 10 questions across all categories:
- Wiki lookups (branch protection, SSH setup)
- Source code reading (framework identification)
- File listing (API routers)
- Data queries (item count)
- API behavior (status codes)
- Bug diagnosis (division by zero, NoneType errors)
- System design (request lifecycle)
- ETL pipeline (idempotency)

## Lessons Learned

1. **Tool descriptions matter:** The LLM chooses tools based on descriptions. Be specific about when to use each tool.

2. **Path security is critical:** Always validate file paths to prevent directory traversal attacks.

3. **Environment separation:** Keep LLM config (`.env.agent.secret`) separate from backend config (`.env.docker.secret`).

4. **Debug output separation:** Send all debug info to stderr, only JSON to stdout for clean parsing.

5. **Error handling:** Comprehensive error handling for network issues, timeouts, and malformed responses prevents crashes.

6. **OpenAI compatibility:** Using the OpenAI-compatible API format makes it easy to switch providers (Qwen Code, OpenRouter, etc.).

7. **Iteration is key:** The agentic loop allows the LLM to refine its approach based on tool results.

8. **Source extraction:** Automatically extracting source references from content improves answer quality.

## Final Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────┐   │
│  │  agent.py    │────▶│  Qwen Code API                   │   │
│  │  (CLI)       │◀────│  (qwen3-coder-plus)              │   │
│  └──────┬───────┘     └──────────────────────────────────┘   │
│         │                                                    │
│         │ tool calls                                         │
│         ├──────────▶ read_file(path) ──▶ source code, wiki/  │
│         ├──────────▶ list_files(dir)  ──▶ files and folders  │
│         ├──────────▶ query_api(method, path) ──▶ backend API │
│         │                                                    │
│  ┌──────┴───────┐                                            │
│  │  Docker      │  app (FastAPI) ─── postgres (data)         │
│  │  Compose     │  caddy (frontend)                          │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
```

## Next Steps (Optional Task 1)

Advanced features to consider:
- Add more tools (search code, run tests, git operations)
- Improve source extraction with better anchor detection
- Add caching for repeated tool calls
- Support streaming responses for long answers
- Add conversation history for multi-turn dialogues
