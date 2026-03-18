# Task 1 Plan: Call an LLM from Code

## LLM Provider and Model

**Provider:** Qwen Code API (self-hosted on VM)
**Model:** `qwen3-coder-plus`

### Why Qwen Code?
- 1000 free requests per day
- Works from Russia without VPN
- No credit card required
- OpenAI-compatible API endpoint

### Configuration
- **API Base:** `http://<vm-ip>:42005/v1` (Qwen Code API proxy on VM)
- **API Key:** Stored in `.env.agent.secret` as `LLM_API_KEY`
- **Model:** `qwen3-coder-plus` (specified in `.env.agent.secret`)

## Agent Architecture

### Components

1. **Environment Configuration**
   - Read `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` from `.env.agent.secret`
   - Use `python-dotenv` to load environment variables

2. **CLI Interface**
   - Accept question as first command-line argument
   - Parse `sys.argv[1]` for the user question

3. **LLM Client**
   - Use `httpx` or `requests` to call the OpenAI-compatible chat completions API
   - Endpoint: `{LLM_API_BASE}/chat/completions`
   - Method: POST
   - Headers: `Authorization: Bearer {LLM_API_KEY}`, `Content-Type: application/json`
   - Body:
     ```json
     {
       "model": "{LLM_MODEL}",
       "messages": [
         {"role": "system", "content": "You are a helpful assistant."},
         {"role": "user", "content": "{question}"}
       ]
     }
     ```

4. **Response Parser**
   - Extract `choices[0].message.content` from the API response
   - Format as JSON output: `{"answer": "...", "tool_calls": []}`

5. **Output Handler**
   - Print JSON to stdout (only valid JSON)
   - Send debug/progress output to stderr
   - Exit code 0 on success

## Data Flow

```
User question (CLI arg)
    ↓
Load env vars from .env.agent.secret
    ↓
Build API request
    ↓
Call LLM API (POST /v1/chat/completions)
    ↓
Parse response (extract content)
    ↓
Format JSON output
    ↓
Print to stdout
```

## Error Handling

- **Missing API key:** Exit with error message to stderr
- **API timeout:** Set 60-second timeout, exit with error
- **Invalid response:** Exit with error message to stderr
- **No question provided:** Show usage message

## Testing Strategy

Create 1 regression test:
- Run `agent.py` with a simple question (e.g., "What is 2+2?")
- Parse stdout as JSON
- Verify `answer` field exists and is non-empty
- Verify `tool_calls` field exists and is an empty array

## Files to Create

1. `plans/task-1.md` - This plan
2. `agent.py` - Main agent CLI
3. `AGENT.md` - Documentation
4. `tests/test_task1.py` - Regression test

## Acceptance Criteria Checklist

- [ ] Plan committed before code
- [ ] `agent.py` exists in project root
- [ ] `uv run agent.py "..."` outputs valid JSON with `answer` and `tool_calls`
- [ ] API key stored in `.env.agent.secret` (not hardcoded)
- [ ] `AGENT.md` documents the solution architecture
- [ ] 1 regression test exists and passes
