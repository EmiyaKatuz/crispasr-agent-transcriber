# Plugin Installation

## For end users

### 1. Install the plugin source

Clone the plugin into the standard personal plugin directory:

```powershell
$pluginRoot = Join-Path $HOME "plugins\crispasr-agent-transcriber"
git clone https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git $pluginRoot
Set-Location $pluginRoot
```

### 2. Install Python dependencies

```powershell
uv sync --extra dev --extra mcp
```

### 3. Install CrispASR binary

```powershell
uv run python scripts/transcribe.py --install-crispasr
```

This auto-detects your hardware:
- **CUDA** — if `nvidia-smi` works or `CUDA_PATH` is set
- **Vulkan** — if `vulkaninfo` is available (only when CUDA is absent)
- **CPU** — fallback

### 4. Download model files

Place these in the `models/` directory:

| Purpose | File | Source |
|---|---|---|
| English ASR | `cohere-transcribe.gguf` | [HuggingFace cstr](https://huggingface.co/cstr) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q2_k.gguf` | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

### 5. Register the personal marketplace entry

Create `%USERPROFILE%\.agents\plugins\marketplace.json` if it does not
already exist. The personal marketplace is discovered automatically by Codex:

```json
{
  "name": "personal",
  "interface": {
    "displayName": "Personal"
  },
  "plugins": [
    {
      "name": "crispasr-agent-transcriber",
      "source": {
        "source": "local",
        "path": "./plugins/crispasr-agent-transcriber"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

If that marketplace file already contains other plugins, append only the new
entry to its existing `plugins` array instead of replacing the file.

Install the plugin in a Codex build that provides plugin commands:

```powershell
codex plugin add crispasr-agent-transcriber@personal
```

In Codex desktop builds without the `codex plugin` CLI command, open the
Plugins view and install **CrispASR Transcriber** from the Personal marketplace.

The plugin provides:
- **Skill**: `crispasr-transcription` (see `skills/crispasr-transcription/SKILL.md`)
- **MCP server**: 6 tools for health, backends, detection, and transcription
- **CLI script**: `scripts/transcribe.py` for direct command-line use

### 6. Verify

```powershell
uv run pytest
uv run ruff check .
uv run python scripts/transcribe.py --crispasr-status
```

## For developers

### Repository structure

```
crispasr-agent-transcriber/
  .codex-plugin/plugin.json    Plugin manifest
  .mcp.json                    MCP server config
  assets/                      Plugin icons and README
  skills/                      Codex Skill definitions
  src/                         Python package
  mcp_server/                  MCP server package
  scripts/                     CLI entry point and setup
  docs/                        Documentation
  examples/                    Usage examples
  tests/                       Test suite
```

### Running the MCP server standalone

```powershell
uv run --extra mcp python -m crispasr_mcp.server
```

### Running the CLI

```powershell
uv run python scripts/transcribe.py file.mp4 --profile auto --manage-server --model models\cohere-transcribe.gguf --lid-backend firered --lid-model models\firered-lid-q2_k.gguf --format srt
```
