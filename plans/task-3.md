# Task 3 Plan: The System Agent

## Overview

Task 3 extends the Task 2 agent with a `query_api` tool to query the deployed backend API. The agent can now answer questions about system facts (framework, ports, status codes) and data-dependent queries (item count, scores).

## New Tool: `query_api`

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Call the backend API to query data or test endpoints. Use this for questions about the running system.",
    "parameters": {
      "type": "object",
      "properties": {
        "method": {
          "type": "string",
          "description": "HTTP method (GET, POST, etc.)"
        },
        "path": {
          "type": "string",
          "description": "API path (e.g., '/items/', '/analytics/completion-rate')"
        },
        "body": {
          "type": "string",
          "description": "Optional JSON request body for POST/PUT requests"
        }
      },
      "required": ["method", "path"]
    }
  }
}
```

### Implementation

```python
def tool_query_api(method: str, path: str, body: str | None = None) -> str:
    """Call the backend API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path
        body: Optional JSON request body
        
    Returns:
        JSON string with status_code and body, or error message.
    """
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    api_key = os.getenv("LMS_API_KEY")
    
    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    if body:
        headers["Content-Type"] = "application/json"
        response = httpx.request(method, url, headers=headers, content=body)
    else:
        response = httpx.request(method, url, headers=headers)
    
    return json.dumps({
        "status_code": response.status_code,
        "body": response.json() if response.content else response.text
    })
```

### Authentication

- Reads `LMS_API_KEY` from environment variables (via `.env.docker.secret`)
- Uses `Authorization: Bearer {LMS_API_KEY}` header
- Reads `AGENT_API_BASE_URL` (defaults to `http://localhost:42002`)

## Environment Variables

| Variable             | Purpose                              | Source                    |
| -------------------- | ------------------------------------ | ------------------------- |
| `LLM_API_KEY`        | LLM provider API key                 | `.env.agent.secret`       |
| `LLM_API_BASE`       | LLM API endpoint URL                 | `.env.agent.secret`       |
| `LLM_MODEL`          | Model name                           | `.env.agent.secret`       |
| `LMS_API_KEY`        | Backend API key for `query_api` auth | `.env.docker.secret`      |
| `AGENT_API_BASE_URL` | Base URL for `query_api`             | Optional, defaults to localhost |

## Updated System Prompt

Add guidance for when to use `query_api`:

```
You have access to these tools:
- list_files(path): List files and directories
- read_file(path): Read a file's contents
- query_api(method, path, body): Call the backend API

Use query_api when:
- Asked about data in the database (e.g., "How many items...?")
- Asked about API behavior (e.g., "What status code...?")
- Asked to query specific endpoints

Use read_file/list_files when:
- Asked about documentation (wiki/)
- Asked about source code (backend/)
- Asked about configuration (docker-compose.yml, etc.)
```

## Agentic Loop Updates

The loop remains the same, just with an additional tool:

1. Send question + all tool definitions to LLM
2. If LLM returns tool calls → execute (including `query_api`)
3. Feed results back
4. Repeat until final answer
5. Output JSON with `answer`, `source` (optional for API queries), `tool_calls`

## Benchmark Evaluation

Run the local benchmark:

```bash
uv run run_eval.py
```

### Expected Results for 10 Questions

| # | Question Type | Tools Required | Expected Answer |
|---|--------------|----------------|-----------------|
| 0 | Wiki lookup | `read_file` | Branch protection steps |
| 1 | Wiki lookup | `read_file` | SSH connection steps |
| 2 | Source code | `read_file` | FastAPI |
| 3 | File listing | `list_files` | API router modules |
| 4 | Data query | `query_api` | Item count (>0) |
| 5 | API behavior | `query_api` | 401/403 status code |
| 6 | Bug diagnosis | `query_api`, `read_file` | ZeroDivisionError |
| 7 | Bug diagnosis | `query_api`, `read_file` | TypeError/NoneType |
| 8 | System design | `read_file` | Request lifecycle (4+ hops) |
| 9 | ETL pipeline | `read_file` | Idempotency via external_id |

## Iteration Strategy

1. **First run:** Identify failing questions
2. **Diagnose:** Check tool calls and answers
3. **Fix:**
   - Tool description too vague → improve schema
   - Wrong tool chosen → update system prompt
   - Tool error → fix implementation
   - Answer format wrong → adjust prompt
4. **Re-run:** Test until all pass

## Testing Strategy

Add 2 regression tests:

1. **Framework question:** "What framework does the backend use?"
   - Expected: `read_file` in tool_calls, answer contains "FastAPI"

2. **Database count:** "How many items are in the database?"
   - Expected: `query_api` in tool_calls, answer contains a number

## Files to Update

1. `plans/task-3.md` - This plan (add benchmark results after first run)
2. `agent.py` - Add `query_api` tool and update system prompt
3. `AGENT.md` - Document `query_api`, authentication, lessons learned
4. `tests/test_agent.py` - Add 2 more tests

## Acceptance Criteria Checklist

- [ ] Plan committed before code
- [ ] `agent.py` defines `query_api` as function-calling schema
- [ ] `query_api` authenticates with `LMS_API_KEY`
- [ ] Agent reads all LLM config from environment variables
- [ ] Agent reads `AGENT_API_BASE_URL` (defaults to localhost)
- [ ] Static system questions answered correctly
- [ ] Data-dependent questions answered with plausible values
- [ ] `run_eval.py` passes all 10 local questions
- [ ] `AGENT.md` documents final architecture (at least 200 words)
- [ ] 2 tool-calling regression tests exist and pass
- [ ] Autochecker bot benchmark passes

## Benchmark Results (to be filled after first run)

Initial score: _/10

First failures:
- Question N: [description]
- Fix applied: [description]

Iteration log:
1. Run 1: _/10 - Fixed: [issue]
2. Run 2: _/10 - Fixed: [issue]
3. Run 3: _/10 - All passed!
