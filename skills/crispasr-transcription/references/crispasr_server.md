# CrispASR Server Reference

Run one backend at a time.

English (Cohere Transcribe):

```powershell
crispasr --server --backend cohere -m models\cohere-transcribe-q4_k.gguf --port 8080
```

Chinese (Qwen3-ASR 1.7B):

```powershell
crispasr --server --backend qwen3-1.7b -m models\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Language detection (FireRed LID):

```powershell
crispasr --backend firered -m models\firered-lid-q4_k.gguf -f audio.wav --detect-language --no-prints
```

Endpoint used by this project:

```text
POST /v1/audio/transcriptions
```
