# LLM Provider Configuration

## Supported Providers

| Provider | Model | Base URL |
|----------|-------|----------|
| `glm` (default) | glm-4.7 | https://open.bigmodel.cn/api/anthropic |
| `minimax` | MiniMax-M2.7 | https://api.minimaxi.com/anthropic |

## Usage

**1. Set provider in `.env`:**
```bash
LLM_PROVIDER=glm      # Use 智谱GLM4.7 (default)
LLM_PROVIDER=minimax  # Use MiniMax-M2.7
```

**2. Configure API token in `.env`:**
```bash
ANTHROPIC_AUTH_TOKEN=your-token-here
```

**3. Optional overrides in `.env`:**
```bash
# Override specific settings (optional)
ANTHROPIC_BASE_URL=https://...
ANTHROPIC_DEFAULT_SONNET_MODEL=custom-model
```

## Provider Settings File

Provider presets are stored in `config/llm_config.json`:
```json
{
  "glm": { "base_url": "...", "model": "glm-4.7" },
  "minimax": { "base_url": "...", "model": "MiniMax-M2.7" }
}
```

## Priority

1. `ANTHROPIC_BASE_URL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` (explicit override)
2. `LLM_PROVIDER` preset from `config/llm_config.json`
3. Hardcoded defaults

## Add New Provider

Edit `config/llm_config.json`:
```json
{
  "glm": { "base_url": "...", "model": "..." },
  "minimax": { "base_url": "...", "model": "..." },
  "newprovider": { "base_url": "...", "model": "..." }
}
```