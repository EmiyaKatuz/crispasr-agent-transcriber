# CrispASR Setup

Install and build CrispASR from its upstream repository:

https://github.com/CrispStrobe/CrispASR

This project expects a local `crispasr` executable. It does not bundle CrispASR or model files.

## Recommended v0.1 models

- English: `cohere-transcribe-q4_k.gguf` with backend `cohere`
- Chinese: `qwen3-asr-1.7b-q4_k.gguf` with backend `qwen3-1.7b`

Place model files in the `models/` directory at the repository root.

```powershell
models\
```

## Start one server

English:

```powershell
crispasr --server --backend cohere -m models\cohere-transcribe-q4_k.gguf --port 8080
```

Chinese:

```powershell
crispasr --server --backend qwen3-1.7b -m models\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Only one is expected at a time.
