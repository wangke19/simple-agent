from __future__ import annotations

import json
import logging
from typing import Any

from simple_agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

COMPACT_SYSTEM_PROMPT = """你是一个对话摘要工具。请将以下对话历史压缩为简洁的摘要，保留所有关键信息：
- 用户请求了什么
- 调用了哪些工具，结果是什么
- 做出了什么决定或结论

请用中文输出摘要，使用要点格式。"""


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """Rough token estimate: ~4 chars per token for mixed Chinese/English."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += len(json.dumps(block, ensure_ascii=False))
    return total // 4


def compact_messages(
    messages: list[dict[str, Any]],
    keep_recent: int,
    llm: LLMClient,
    max_context_tokens: int,
    compact_threshold: float,
) -> list[dict[str, Any]]:
    """Compact old messages if token count exceeds threshold.

    Returns the (potentially compacted) message list.
    """
    threshold = int(max_context_tokens * compact_threshold)
    current_tokens = estimate_tokens(messages)

    if current_tokens < threshold:
        return messages

    logger.info(
        "Context tokens %d exceeds threshold %d, compacting",
        current_tokens, threshold,
    )

    if len(messages) <= keep_recent:
        return messages

    old_messages = messages[:-keep_recent]
    recent_messages = messages[-keep_recent:]

    summary = _summarize(old_messages, llm)

    compacted = [{"role": "user", "content": f"之前的对话摘要：\n{summary}"}]
    compacted.extend(recent_messages)

    logger.info(
        "Compacted %d messages into summary, kept %d recent",
        len(old_messages), keep_recent,
    )
    return compacted


def _summarize(messages: list[dict[str, Any]], llm: LLMClient) -> str:
    """Use the LLM to summarize a list of messages."""
    formatted = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        parts.append(f"[调用工具: {block.get('name', '')}({json.dumps(block.get('input', {}), ensure_ascii=False)})]")
                    elif block.get("type") == "tool_result":
                        parts.append(f"[工具结果: {block.get('content', '')}]")
            content = "\n".join(parts)
        formatted.append(f"{role}: {content}")

    conversation = "\n\n".join(formatted)

    try:
        response = llm.call(
            system_prompt=COMPACT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": conversation}],
        )
        return response.content[0].text
    except Exception as e:
        logger.warning("Failed to compact messages: %s", e)
        return "（摘要生成失败）"
