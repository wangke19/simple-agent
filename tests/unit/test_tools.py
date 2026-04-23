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

    def test_format_descriptions(self):
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(CalculatorTool())
        desc = registry.format_descriptions()
        assert "search: 搜索信息" in desc
        assert "calculate: 计算数学表达式" in desc

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(SearchTool())
        assert len(registry.list_tools()) == 1


class TestSearchTool:
    def test_execute(self):
        tool = SearchTool()
        result = tool.execute("北京天气")
        assert "北京" in result
        assert "25度" in result

    def test_properties(self):
        tool = SearchTool()
        assert tool.name == "search"
        assert tool.description == "搜索信息"


class TestCalculatorTool:
    def test_execute(self):
        tool = CalculatorTool()
        assert tool.execute("2 + 3") == "5"
        assert tool.execute("10 * 2") == "20"

    def test_execute_invalid_raises(self):
        tool = CalculatorTool()
        with pytest.raises(ToolError, match="计算错误"):
            tool.execute("invalid_expr__$%")

    def test_properties(self):
        tool = CalculatorTool()
        assert tool.name == "calculate"
        assert tool.description == "计算数学表达式"
