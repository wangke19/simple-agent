import pytest

from simple_agent.exceptions import ToolError
from simple_agent.tools import CalculatorTool, SearchTool, ToolRegistry
from simple_agent.tools.base import BaseTool


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = SearchTool()
        registry.register(tool)
        assert registry.get("search") is tool

    def test_register_duplicate_raises(self):
        registry = ToolRegistry()
        registry.register(SearchTool())
        with pytest.raises(ToolError, match="already registered"):
            registry.register(SearchTool())

    def test_get_unknown_raises(self):
        registry = ToolRegistry()
        with pytest.raises(ToolError, match="Unknown tool"):
            registry.get("nonexistent")

    def test_to_api_format(self):
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(CalculatorTool())
        api_tools = registry.to_api_format()
        assert len(api_tools) == 2
        names = {t["name"] for t in api_tools}
        assert names == {"search", "calculate"}
        for t in api_tools:
            assert "name" in t
            assert "description" in t
            assert "input_schema" in t

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(SearchTool())
        assert len(registry.list_tools()) == 1


class TestSearchTool:
    def test_execute(self):
        tool = SearchTool()
        result = tool.execute(input="weather")
        assert "weather" in result

    def test_properties(self):
        tool = SearchTool()
        assert tool.name == "search"
        assert tool.description == "Search for information (placeholder)."

    def test_parameters_schema(self):
        tool = SearchTool()
        schema = tool.parameters
        assert schema["type"] == "object"
        assert "input" in schema["properties"]


class TestCalculatorTool:
    def test_execute(self):
        tool = CalculatorTool()
        assert tool.execute(input="2 + 3") == "5"
        assert tool.execute(input="10 * 2") == "20"

    def test_execute_invalid_raises(self):
        tool = CalculatorTool()
        with pytest.raises(ToolError, match="Evaluation error"):
            tool.execute(input="invalid_expr__$%")

    def test_properties(self):
        tool = CalculatorTool()
        assert tool.name == "calculate"
        assert tool.description == "Evaluate a mathematical expression."

    def test_parameters_schema(self):
        tool = CalculatorTool()
        schema = tool.parameters
        assert schema["type"] == "object"
        assert "input" in schema["properties"]
