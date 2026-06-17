# CrispASR Server Reference

Run one backend at a time.

English:

```powershell
crispasr --server --backend cohere -m C:\models\cohere-transcribe-q4_k.gguf --port 8080
```

Chinese:

```powershell
crispasr --server --backend qwen3-1.7b -m C:\models\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Endpoint used by this project:

```text
POST /v1/audio/transcriptions
```
