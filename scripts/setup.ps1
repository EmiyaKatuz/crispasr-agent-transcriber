# crispasr-agent-transcriber setup
# Downloads CrispASR binary and prints model download instructions.
# Usage: .\scripts\setup.ps1
#
# This is a thin wrapper — the real logic lives in crispasr_manager.py.
# Run it standalone or via:
#   uv run python scripts/transcribe.py --install-crispasr

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "crispasr-agent-transcriber setup"
Write-Host ""

Write-Host "[...] installing CrispASR binary ..."
uv run python scripts/transcribe.py --install-crispasr

Write-Host ""
Write-Host "=== Next: download models ==="
Write-Host ""
Write-Host "English ASR (Cohere Transcribe 03-2026):"
Write-Host "  Recommended: cohere-transcribe-03-2026-q4_k.gguf"
Write-Host "  Browse: https://huggingface.co/cstr"
Write-Host ""
Write-Host "Chinese ASR (Qwen3-ASR 1.7B):"
Write-Host "  Recommended: qwen3-asr-1.7b-q4_k.gguf"
Write-Host "  Browse: https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF"
Write-Host ""
Write-Host "Language detection (Silero LID 95 languages):"
Write-Host "  Recommended: silero-lid-95-f16.gguf (~1.5 MB)"
Write-Host "  Browse: https://huggingface.co/cstr/silero-lid-95-GGUF"
Write-Host ""
Write-Host "Place model files in the `models/` directory at the repository root.
Write-Host "Then pass --model models\<file>.gguf when transcribing."