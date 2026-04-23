from __future__ import annotations

TOOL_CALL_FORMAT = '{"type":"tool", "tool":"工具名", "input":"参数"}'
ANSWER_FORMAT = '{"type":"answer", "content":"答案内容"}'

SYSTEM_PROMPT_TEMPLATE = """你有这些工具：
{tool_list}

回复JSON格式：
使用工具：{tool_format}
给出答案：{answer_format}"""


def build_system_prompt(tool_list: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        tool_list=tool_list,
        tool_format=TOOL_CALL_FORMAT,
        answer_format=ANSWER_FORMAT,
    )
