"""Configurable prompt templates for the agent and workflow."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Prompts:
    """All LLM-facing prompt templates with English defaults."""

    # Agent defaults
    default_system_prompt: str = (
        "You are an AI assistant that can use tools to complete tasks. "
        "Call tools as needed, or give a direct answer."
    )
    resume_guidance_template: str = (
        "Human guidance: {guidance}\n\nPlease continue the task."
    )

    # Workflow: planning
    plan_prompt: str = (
        "You are a project planning expert. Create a development plan for the following task.\n"
        "\n"
        "Output format (follow strictly):\n"
        "1. First a '## Requirements Analysis' section, briefly describing what to build\n"
        "2. Then a '## Task Breakdown' section, listing atomic tasks, one per line:\n"
        "   - [Task number] Task description\n"
        "   Each task should be independent, verifiable, and small\n"
        "3. Output nothing else"
    )

    # Workflow: decomposition
    decompose_prompt: str = (
        "Based on the following plan, break it down into specific atomic tasks.\n"
        "Each task must be:\n"
        "- Independent: can be executed and verified alone\n"
        "- Small: one file write or one command execution\n"
        "- Ordered: with clear dependencies\n"
        "\n"
        "Output format (follow strictly), one task per line:\n"
        "1. Create xxx file with yyy functionality [depends: none]\n"
        "2. Create zzz file with www functionality [depends: 1]\n"
        "3. Run tests to verify [depends: 1, 2]\n"
        "\n"
        "For each task, add [depends: N, M] listing which task numbers must complete first.\n"
        "Use [depends: none] for the first task(s) with no prerequisites.\n"
        "Output only the numbered list, nothing else."
    )
    decompose_context_template: str = (
        "Original requirement: {requirement}\n\nInitial plan:\n{plan}"
    )

    # Workflow: API contracts
    contract_prompt: str = (
        "You are an interface design expert. Based on the requirements and task list, "
        "define interface contracts between all modules.\n"
        "\n"
        "Requirements:\n"
        "1. Analyze each module (file) in the task list\n"
        "2. For each module, list all public function/method signatures\n"
        "3. Signatures must include: method name, parameter names, parameter types, return type\n"
        "4. If module A calls module B, explicitly write out the call relationship\n"
        "5. Parameter names and types must be consistent with no ambiguity\n"
        "\n"
        "Output format (follow strictly):\n"
        "\n"
        "## Module Interface Contracts\n"
        "\n"
        "### <filename> - <class or module name>\n"
        "Method signatures, one per line:\n"
        "- <method_name>(<param>: <type>, ...) -> <return_type>\n"
        "- ...\n"
        "\n"
        "### <another_filename>\n"
        "Imports from <filename>: <specific imports>\n"
        "Call relationships:\n"
        "- Calls <module>.<method>(<param description>)\n"
        "- ...\n"
        "\n"
        "Output only the contract, nothing else."
    )
    contract_context_template: str = (
        "Original requirement: {requirement}\n\n"
        "Initial plan:\n{plan}\n\n"
        "Task list:\n{task_list}"
    )
    contract_injection_template: str = (
        "\n\n---\n"
        "## API Contract (shared interface spec — strictly follow method names and parameters)\n"
        "{contract}\n"
        "---"
    )
    schema_injection_template: str = (
        "\n\n---\n"
        "## Database Schema (GROUND TRUTH — all SQL must use these EXACT table and column names)\n"
        "When writing SQL queries, you MUST use the column names defined below. Do NOT invent column names.\n"
        "Pay special attention to: primary key column names, foreign key column names, and column naming conventions.\n"
        "{schema}\n"
        "---"
    )
    rules_injection_template: str = (
        "\n\n---\n"
        "## Project Rules (from AGENT.md — STRICTLY follow all rules below)\n"
        "{rules}\n"
        "---\n"
        "## Engineering Standards (non-negotiable)\n"
        "{engineering_standards}\n"
        "---"
    )

    # Compaction
    compact_system_prompt: str = (
        "You are a conversation summarizer. Compress the following conversation history "
        "into a concise summary, preserving all key information:\n"
        "- What the user requested\n"
        "- Which tools were called and their results\n"
        "- What decisions or conclusions were made\n"
        "\n"
        "Output the summary in bullet-point format."
    )
    compact_summary_prefix: str = "Previous conversation summary:\n{summary}"
    compact_tool_call_label: str = "[Tool call: {name}({input})]"
    compact_tool_result_label: str = "[Tool result: {content}]"
    compact_failed_fallback: str = "(Summary generation failed)"


def chinese_prompts() -> Prompts:
    """Return Prompts with Chinese defaults (backward compatibility)."""
    return Prompts(
        default_system_prompt=(
            "你是一个AI助手，可以使用工具来完成任务。请根据需要调用工具，或直接给出答案。"
        ),
        resume_guidance_template="人类指导：{guidance}\n\n请继续完成任务。",
        plan_prompt=(
            "你是一个项目规划专家。请为以下任务创建开发计划。\n"
            "\n"
            "输出格式要求（严格遵守）：\n"
            "1. 先输出'## 需求分析'段落，简述要做什么\n"
            "2. 然后输出'## 任务拆解'段落，列出原子任务，每个任务一行，格式为：\n"
            "   - [任务编号] 任务描述\n"
            "   每个任务应该是一个独立的、可验证的小步骤\n"
            "3. 不要输出其他内容"
        ),
        decompose_prompt=(
            "根据以下计划，请把任务拆解为具体的原子任务列表。\n"
            "每个任务必须是：\n"
            "- 独立的：可以单独执行和验证\n"
            "- 小的：一次文件写入或一次命令执行\n"
            "- 有序的：有明确的先后依赖\n"
            "\n"
            "输出格式（严格遵守），每行一个任务：\n"
            "1. 创建 xxx 文件，包含 yyy 功能 [depends: none]\n"
            "2. 创建 zzz 文件，包含 www 功能 [depends: 1]\n"
            "3. 运行测试验证 [depends: 1, 2]\n"
            "\n"
            "每个任务添加 [depends: N, M] 标注其依赖的前置任务编号。\n"
            "无前置依赖的任务使用 [depends: none]。\n"
            "只输出编号列表，不要其他内容。"
        ),
        decompose_context_template="原始需求：{requirement}\n\n初步计划：\n{plan}",
        contract_prompt=(
            "你是一个接口设计专家。根据需求和任务列表，定义所有模块之间的接口契约。\n"
            "\n"
            "要求：\n"
            "1. 分析任务列表中涉及的每个模块（文件）\n"
            "2. 对每个模块，列出所有公开函数/方法的完整签名\n"
            "3. 签名必须包含：方法名、参数名、参数类型、返回类型\n"
            "4. 如果模块A调用模块B，必须明确写出调用关系\n"
            "5. 参数名和类型必须前后一致，不能有歧义\n"
            "\n"
            "输出格式（严格遵守）：\n"
            "\n"
            "## 模块接口契约\n"
            "\n"
            "### <文件名> - <类名或模块名>\n"
            "方法签名列表，每个方法一行：\n"
            "- <方法名>(<参数名>: <类型>, ...) -> <返回类型>\n"
            "- ...\n"
            "\n"
            "### <另一个文件名>\n"
            "从 <文件名> 导入: <具体导入内容>\n"
            "调用关系：\n"
            "- 调用 <模块>.<方法>(<参数说明>)\n"
            "- ...\n"
            "\n"
            "只输出契约内容，不要输出其他解释。"
        ),
        contract_context_template=(
            "原始需求：{requirement}\n\n初步计划：\n{plan}\n\n任务列表：\n{task_list}"
        ),
        contract_injection_template=(
            "\n\n---\n"
            "## 接口契约（以下是你和其他任务共同遵守的接口规范，"
            "必须严格按照契约中的方法名和参数调用）\n"
            "{contract}\n"
            "---"
        ),
        schema_injection_template=(
            "\n\n---\n"
            "## 数据库 Schema（以下是最终权威定义 — 所有 SQL 必须使用这里的精确表名和列名）\n"
            "编写 SQL 查询时，必须使用下面定义的列名，不得自行发明列名。\n"
            "特别注意：主键列名、外键列名、列命名风格。\n"
            "{schema}\n"
            "---"
        ),
        rules_injection_template=(
            "\n\n---\n"
            "## 项目规则（来自 AGENT.md — 必须严格遵守以下所有规则）\n"
            "{rules}\n"
            "---\n"
            "## 工程标准（不可违反）\n"
            "{engineering_standards}\n"
            "---"
        ),
        compact_system_prompt=(
            "你是一个对话摘要工具。请将以下对话历史压缩为简洁的摘要，保留所有关键信息：\n"
            "- 用户请求了什么\n"
            "- 调用了哪些工具，结果是什么\n"
            "- 做出了什么决定或结论\n"
            "\n"
            "请用中文输出摘要，使用要点格式。"
        ),
        compact_summary_prefix="之前的对话摘要：\n{summary}",
        compact_tool_call_label="[调用工具: {name}({input})]",
        compact_tool_result_label="[工具结果: {content}]",
        compact_failed_fallback="（摘要生成失败）",
    )
