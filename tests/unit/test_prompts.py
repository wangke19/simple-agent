from simple_agent.prompts import Prompts, chinese_prompts


def test_default_prompts_are_english():
    p = Prompts()
    assert "AI assistant" in p.default_system_prompt
    assert "planning expert" in p.plan_prompt
    assert "atomic tasks" in p.decompose_prompt
    assert "interface design expert" in p.contract_prompt
    assert "conversation summarizer" in p.compact_system_prompt


def test_default_prompts_non_empty():
    p = Prompts()
    for field in [
        "default_system_prompt", "resume_guidance_template",
        "plan_prompt", "decompose_prompt", "decompose_context_template",
        "contract_prompt", "contract_context_template", "contract_injection_template",
        "compact_system_prompt", "compact_summary_prefix",
        "compact_tool_call_label", "compact_tool_result_label",
        "compact_failed_fallback",
    ]:
        assert len(getattr(p, field)) > 0


def test_chinese_prompts():
    p = chinese_prompts()
    assert "AI助手" in p.default_system_prompt
    assert "项目规划专家" in p.plan_prompt


def test_individual_override():
    p = Prompts(default_system_prompt="Custom prompt")
    assert p.default_system_prompt == "Custom prompt"
    assert "planning expert" in p.plan_prompt  # others unchanged


def test_template_formatting():
    p = Prompts()
    result = p.resume_guidance_template.format(guidance="try again")
    assert "try again" in result

    result = p.contract_injection_template.format(contract="some contract")
    assert "some contract" in result
