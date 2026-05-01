# LLM Provider Switching Design

## Overview

Add environment variable `LLM_PROVIDER` to switch between LLM providers without code changes.

## Providers

| LLM_PROVIDER | Base URL | Model |
|--------------|----------|-------|
| `glm` | `https://open.bigmodel.cn/api/anthropic` | `glm-4.7` |
| `minimax` | `https://api.minimaxi.com/anthropic` | `MiniMax-M2.7` |

## Usage

```bash
LLM_PROVIDER=glm     # 智谱GLM4.7
LLM_PROVIDER=minimax # MiniMax-M2.7
```

## Priority

1. `ANTHROPIC_BASE_URL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` (explicit override, highest)
2. `LLM_PROVIDER` preset (convenience switch)
3. Hardcoded defaults (fallback)

## Files to Modify

- `src/simple_agent/config.py` — parse `LLM_PROVIDER`, apply preset defaults
- `.env.example` — document `LLM_PROVIDER` and presets