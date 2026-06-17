# CrispASR Setup

Install and build CrispASR from its upstream repository:

https://github.com/CrispStrobe/CrispASR

This project expects a local `crispasr` executable. It does not bundle CrispASR or model files.
Use `--install-crispasr` to download the latest binary automatically (auto-detects GPU).

## Recommended v0.1 models

| Purpose | File | Backend |
|---|---|---|
| English ASR | `cohere-transcribe.gguf` | `cohere` |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | `qwen3-1.7b` |
| Language detection | `firered-lid-q2_k.gguf` | `firered` |

Place model files in the `models/` directory at the repository root.

## Start one server

English (Cohere Transcribe):

```powershell
crispasr --server --backend cohere -m models\cohere-transcribe.gguf --port 8080
```

Chinese (Qwen3-ASR 1.7B):

```powershell
crispasr --server --backend qwen3-1.7b -m models\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Only one is expected at a time. The tool auto-selects the correct backend
based on language detection or the chosen profile.