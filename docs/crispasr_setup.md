# CrispASR Setup

Install and build CrispASR from its upstream repository:

https://github.com/CrispStrobe/CrispASR

This project expects a local `crispasr` executable. It does not bundle CrispASR or model files.

## Recommended v0.1 models

- English: `cohere-transcribe-q4_k.gguf` with backend `cohere`
- Chinese: `qwen3-asr-1.7b-q4_k.gguf` with backend `qwen3-1.7b`

Keep models outside this repository, for example:

```powershell
C:\models\crispasr\
```

## Start one server

English:

```powershell
crispasr --server --backend cohere -m C:\models\crispasr\cohere-transcribe-q4_k.gguf --port 8080
```

Chinese:

```powershell
crispasr --server --backend qwen3-1.7b -m C:\models\crispasr\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Only one is expected at a time.
