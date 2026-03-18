"""
Regression tests for the agent.

Run with: uv run pytest tests/ -v
"""

import json
import subprocess
import sys


def run_agent(question: str) -> tuple[str, int]:
    """Run the agent with a question and return (stdout, return_code)."""
    result = subprocess.run(
        [sys.executable, "-m", "uv", "run", "agent.py", question],
        capture_output=True,
        text=True,
    )
    return result.stdout, result.returncode


class TestTask1:
    """Task 1: Call an LLM from Code - Basic LLM integration tests."""

    def test_agent_returns_json_with_answer_and_tool_calls(self):
        """Test that agent returns valid JSON with required fields."""
        # Run the agent with a simple question
        stdout, return_code = run_agent("What is 2+2? Answer with just the number.")

        # Check exit code
        assert return_code == 0, f"Agent exited with code {return_code}"

        # Parse JSON output
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as e:
            assert False, f"Agent output is not valid JSON: {e}\nOutput: {stdout}"

        # Check required fields
        assert "answer" in result, "Missing 'answer' field in output"
        assert "tool_calls" in result, "Missing 'tool_calls' field in output"

        # Check field types
        assert isinstance(result["answer"], str), "'answer' should be a string"
        assert isinstance(result["tool_calls"], list), "'tool_calls' should be an array"

        # Check that answer is non-empty
        assert len(result["answer"]) > 0, "'answer' should not be empty"

        # For Task 1, tool_calls should be empty
        assert result["tool_calls"] == [], "tool_calls should be empty for Task 1"

        # Check that the answer contains "4" (the correct answer)
        assert "4" in result["answer"], (
            f"Expected answer to contain '4', got: {result['answer']}"
        )


class TestTask2:
    """Task 2: The Documentation Agent - Tool calling tests."""

    def test_merge_conflict_question(self):
        """Test that agent uses read_file to answer merge conflict question."""
        stdout, return_code = run_agent("How do you resolve a merge conflict?")

        # Check exit code
        assert return_code == 0, f"Agent exited with code {return_code}"

        # Parse JSON output
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as e:
            assert False, f"Agent output is not valid JSON: {e}\nOutput: {stdout}"

        # Check required fields
        assert "answer" in result, "Missing 'answer' field"
        assert "source" in result, "Missing 'source' field"
        assert "tool_calls" in result, "Missing 'tool_calls' field"

        # Check that tool_calls is populated
        assert len(result["tool_calls"]) > 0, "tool_calls should not be empty"

        # Check that read_file was used
        tool_names = [tc.get("tool") for tc in result["tool_calls"]]
        assert "read_file" in tool_names, "Expected read_file to be called"

        # Check that source mentions wiki
        assert (
            "wiki" in result["source"].lower() or "git" in result["source"].lower()
        ), f"Expected source to mention wiki or git, got: {result['source']}"

    def test_wiki_listing_question(self):
        """Test that agent uses list_files to answer wiki listing question."""
        stdout, return_code = run_agent("What files are in the wiki?")

        # Check exit code
        assert return_code == 0, f"Agent exited with code {return_code}"

        # Parse JSON output
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as e:
            assert False, f"Agent output is not valid JSON: {e}\nOutput: {stdout}"

        # Check required fields
        assert "answer" in result, "Missing 'answer' field"
        assert "source" in result, "Missing 'source' field"
        assert "tool_calls" in result, "Missing 'tool_calls' field"

        # Check that tool_calls is populated
        assert len(result["tool_calls"]) > 0, "tool_calls should not be empty"

        # Check that list_files was used
        tool_names = [tc.get("tool") for tc in result["tool_calls"]]
        assert "list_files" in tool_names, "Expected list_files to be called"


class TestTask3:
    """Task 3: The System Agent - API querying tests."""

    def test_framework_question(self):
        """Test that agent uses read_file to find framework info from source code."""
        stdout, return_code = run_agent(
            "What Python web framework does the backend use?"
        )

        # Check exit code
        assert return_code == 0, f"Agent exited with code {return_code}"

        # Parse JSON output
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as e:
            assert False, f"Agent output is not valid JSON: {e}\nOutput: {stdout}"

        # Check required fields
        assert "answer" in result, "Missing 'answer' field"
        assert "tool_calls" in result, "Missing 'tool_calls' field"

        # Check that answer mentions FastAPI
        assert "fastapi" in result["answer"].lower(), (
            f"Expected answer to mention FastAPI, got: {result['answer']}"
        )

    def test_database_count_question(self):
        """Test that agent uses query_api to count items in database."""
        stdout, return_code = run_agent("How many items are in the database?")

        # Check exit code
        assert return_code == 0, f"Agent exited with code {return_code}"

        # Parse JSON output
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as e:
            assert False, f"Agent output is not valid JSON: {e}\nOutput: {stdout}"

        # Check required fields
        assert "answer" in result, "Missing 'answer' field"
        assert "tool_calls" in result, "Missing 'tool_calls' field"

        # Check that tool_calls is populated
        assert len(result["tool_calls"]) > 0, "tool_calls should not be empty"

        # Check that query_api was used
        tool_names = [tc.get("tool") for tc in result["tool_calls"]]
        assert "query_api" in tool_names, "Expected query_api to be called"

        # Check that answer contains a number
        import re

        numbers = re.findall(r"\d+", result["answer"])
        assert len(numbers) > 0, (
            f"Expected answer to contain a number, got: {result['answer']}"
        )
