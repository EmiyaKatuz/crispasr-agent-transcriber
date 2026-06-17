from __future__ import annotations

import httpx

from crispasr_agent_transcriber.client import CrispASRClient
from crispasr_agent_transcriber.schemas import TranscriptionOptions

from .helpers import write_tone_wav


def test_health_reads_backend() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "backend": "cohere"})

    client = CrispASRClient("http://127.0.0.1:8080", transport=httpx.MockTransport(handler))
    assert client.health().backend == "cohere"


def test_transcribe_posts_audio_and_returns_text(tmp_path) -> None:
    wav_path = write_tone_wav(tmp_path / "tone.wav")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/audio/transcriptions"
        body = request.read()
        assert b'response_format"\r\n\r\ntext' in body
        return httpx.Response(200, text="hello world")

    client = CrispASRClient("http://127.0.0.1:8080", transport=httpx.MockTransport(handler))
    text, raw = client.transcribe(wav_path, TranscriptionOptions(response_format="text"))
    assert text == "hello world"
    assert raw == "hello world"
