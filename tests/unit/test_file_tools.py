import os
import pytest
from pathlib import Path

from simple_agent.tools.file_read import ReadTool
from simple_agent.tools.file_write import WriteTool
from simple_agent.tools.file_edit import EditTool
from simple_agent.tools.file_grep import GrepTool


@pytest.fixture
def workdir(tmp_path):
    return tmp_path


# --- ReadTool ---

class TestReadTool:
    def test_read_full_file(self, workdir):
        (workdir / "test.txt").write_text("line1\nline2\nline3")
        tool = ReadTool(working_dir=workdir)
        result = tool.execute(path="test.txt")
        assert "1\tline1" in result
        assert "3\tline3" in result

    def test_read_with_offset(self, workdir):
        (workdir / "test.txt").write_text("line1\nline2\nline3\nline4")
        tool = ReadTool(working_dir=workdir)
        result = tool.execute(path="test.txt", offset=2)
        assert "2\tline2" in result
        assert "line1" not in result

    def test_read_with_limit(self, workdir):
        (workdir / "test.txt").write_text("line1\nline2\nline3\nline4")
        tool = ReadTool(working_dir=workdir)
        result = tool.execute(path="test.txt", offset=1, limit=2)
        assert "line1" in result
        assert "line2" in result
        assert "line3" not in result

    def test_read_nonexistent_file(self, workdir):
        tool = ReadTool(working_dir=workdir)
        with pytest.raises(FileNotFoundError):
            tool.execute(path="nope.txt")

    def test_read_path_escape(self, workdir):
        tool = ReadTool(working_dir=workdir)
        with pytest.raises(ValueError, match="escapes"):
            tool.execute(path="../../etc/passwd")

    def test_parameters_schema(self):
        schema = ReadTool().parameters
        assert "path" in schema["properties"]
        assert schema["required"] == ["path"]


# --- WriteTool ---

class TestWriteTool:
    def test_write_new_file(self, workdir):
        tool = WriteTool(working_dir=workdir)
        result = tool.execute(path="new.txt", content="hello world")
        assert (workdir / "new.txt").read_text() == "hello world"
        assert "Written" in result

    def test_write_creates_parent_dirs(self, workdir):
        tool = WriteTool(working_dir=workdir)
        tool.execute(path="sub/dir/file.txt", content="nested")
        assert (workdir / "sub" / "dir" / "file.txt").read_text() == "nested"

    def test_write_overwrites_existing(self, workdir):
        (workdir / "existing.txt").write_text("old")
        tool = WriteTool(working_dir=workdir)
        tool.execute(path="existing.txt", content="new")
        assert (workdir / "existing.txt").read_text() == "new"

    def test_write_path_escape(self, workdir):
        tool = WriteTool(working_dir=workdir)
        with pytest.raises(ValueError, match="escapes"):
            tool.execute(path="/tmp/evil.txt", content="nope")

    def test_parameters_schema(self):
        schema = WriteTool().parameters
        assert "path" in schema["properties"]
        assert "content" in schema["properties"]


# --- EditTool ---

class TestEditTool:
    def test_edit_replaces_string(self, workdir):
        (workdir / "test.py").write_text("def hello():\n    pass\n")
        tool = EditTool(working_dir=workdir)
        result = tool.execute(path="test.py", old_string="pass", new_string="return 42")
        assert (workdir / "test.py").read_text() == "def hello():\n    return 42\n"
        assert "Replaced" in result

    def test_edit_old_string_not_found(self, workdir):
        (workdir / "test.py").write_text("hello")
        tool = EditTool(working_dir=workdir)
        with pytest.raises(ValueError, match="not found"):
            tool.execute(path="test.py", old_string="missing", new_string="x")

    def test_edit_ambiguous_match(self, workdir):
        (workdir / "test.py").write_text("foo\nfoo\n")
        tool = EditTool(working_dir=workdir)
        with pytest.raises(ValueError, match="matches 2 times"):
            tool.execute(path="test.py", old_string="foo", new_string="bar")

    def test_edit_nonexistent_file(self, workdir):
        tool = EditTool(working_dir=workdir)
        with pytest.raises(FileNotFoundError):
            tool.execute(path="nope.py", old_string="a", new_string="b")

    def test_edit_path_escape(self, workdir):
        tool = EditTool(working_dir=workdir)
        with pytest.raises(ValueError, match="escapes"):
            tool.execute(path="../../etc/hosts", old_string="a", new_string="b")

    def test_parameters_schema(self):
        schema = EditTool().parameters
        assert "old_string" in schema["properties"]
        assert "new_string" in schema["properties"]


# --- GrepTool ---

class TestGrepTool:
    def test_grep_finds_matches(self, workdir):
        (workdir / "a.py").write_text("def hello():\n    pass\n")
        (workdir / "b.py").write_text("def world():\n    pass\n")
        tool = GrepTool(working_dir=workdir)
        result = tool.execute(pattern="def \\w+")
        assert "a.py" in result
        assert "b.py" in result
        assert "hello" in result
        assert "world" in result

    def test_grep_with_glob(self, workdir):
        (workdir / "a.py").write_text("TARGET\n")
        (workdir / "b.txt").write_text("TARGET\n")
        tool = GrepTool(working_dir=workdir)
        result = tool.execute(pattern="TARGET", glob="*.py")
        assert "a.py" in result
        assert "b.txt" not in result

    def test_grep_no_matches(self, workdir):
        (workdir / "a.py").write_text("hello")
        tool = GrepTool(working_dir=workdir)
        result = tool.execute(pattern="nonexistent_pattern_xyz")
        assert result == "No matches found"

    def test_grep_skips_dotdirs(self, workdir):
        dotdir = workdir / ".hidden"
        dotdir.mkdir()
        (dotdir / "secret.py").write_text("SECRET\n")
        (workdir / "public.py").write_text("PUBLIC\n")
        tool = GrepTool(working_dir=workdir)
        result = tool.execute(pattern="SECRET|PUBLIC")
        assert "SECRET" not in result
        assert "PUBLIC" in result

    def test_grep_in_subdirectory(self, workdir):
        sub = workdir / "src"
        sub.mkdir()
        (sub / "main.py").write_text("import os\n")
        tool = GrepTool(working_dir=workdir)
        result = tool.execute(pattern="import", path="src")
        assert "main.py" in result

    def test_parameters_schema(self):
        schema = GrepTool().parameters
        assert "pattern" in schema["required"]
