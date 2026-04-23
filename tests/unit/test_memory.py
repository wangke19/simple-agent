import pytest
from pathlib import Path

from simple_agent.tools.memory import MemoryTool


@pytest.fixture
def tool(tmp_path):
    return MemoryTool(memory_dir=tmp_path / ".agent")


@pytest.fixture
def tool_with_memories(tool):
    tool._save("用户喜欢中文")
    tool._save("项目使用Python 3.11")
    return tool


class TestMemorySave:
    def test_save_creates_file(self, tool, tmp_path):
        result = tool.execute(action="save", content="test fact")
        assert "Saved" in result
        assert (tmp_path / ".agent" / "memory.md").exists()

    def test_save_appends(self, tool):
        tool.execute(action="save", content="first")
        tool.execute(action="save", content="second")
        content = tool._read_all()
        assert "first" in content
        assert "second" in content

    def test_save_strips_whitespace(self, tool):
        tool.execute(action="save", content="  spaced  ")
        content = tool._read_all()
        assert "- spaced" in content


class TestMemoryRecall:
    def test_recall_empty(self, tool):
        result = tool.execute(action="recall")
        assert result == "(no memories)"

    def test_recall_returns_all(self, tool_with_memories):
        result = tool_with_memories.execute(action="recall")
        assert "中文" in result
        assert "Python" in result


class TestMemoryForget:
    def test_forget_removes_matching(self, tool_with_memories):
        result = tool_with_memories.execute(action="forget", content="Python")
        assert "Removed 1" in result
        remaining = tool_with_memories._read_all()
        assert "Python" not in remaining
        assert "中文" in remaining

    def test_forget_no_match(self, tool_with_memories):
        result = tool_with_memories.execute(action="forget", content="nonexistent")
        assert "Removed 0" in result

    def test_forget_empty_memory(self, tool):
        result = tool.execute(action="forget", content="anything")
        assert "Nothing to forget" in result

    def test_forget_is_case_insensitive(self, tool):
        tool.execute(action="save", content="Hello World")
        result = tool.execute(action="forget", content="hello")
        assert "Removed 1" in result


class TestMemorySystemPrompt:
    def test_load_into_prompt_empty(self, tool):
        assert tool.load_into_system_prompt() == ""

    def test_load_into_prompt_with_data(self, tool):
        tool.execute(action="save", content="test fact")
        prompt = tool.load_into_system_prompt()
        assert "你记住的信息" in prompt
        assert "test fact" in prompt


class TestMemoryParameters:
    def test_parameters_schema(self):
        schema = MemoryTool().parameters
        assert "action" in schema["properties"]
        assert schema["properties"]["action"]["type"] == "string"
        assert "save" in schema["properties"]["action"]["enum"]
