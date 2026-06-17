from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .errors import CrispASRRequestError, ServerError
from .schemas import HealthStatus, TranscriptionOptions

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_server_url(base_url: str, *, allow_remote: bool = False) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ServerError("CrispASR server URL must be an absolute http(s) URL.", url=base_url)
    host = parsed.hostname
    if not allow_remote and host not in LOCAL_HOSTS:
        raise ServerError(
            "Remote CrispASR server URLs are blocked by default.",
            url=base_url,
            hint="Use --allow-remote-server only when you trust that server.",
        )
    return base_url.rstrip("/")


class CrispASRClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        allow_remote: bool = False,
        timeout_seconds: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = validate_server_url(base_url, allow_remote=allow_remote)
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> CrispASRClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def health(self) -> HealthStatus:
        try:
            response = self._client.get("/health", headers=self._headers())
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ServerError(
                "Could not reach CrispASR server health endpoint.",
                url=self.base_url,
            ) from exc
        raw = response.json()
        return HealthStatus(
            status=raw.get("status"),
            backend=raw.get("backend") or raw.get("active"),
            raw=raw,
        )

    def backends(self) -> dict:
        try:
            response = self._client.get("/backends", headers=self._headers())
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ServerError("Could not read CrispASR backends.", url=self.base_url) from exc
        return response.json()

    def transcribe(self, audio_path: Path, options: TranscriptionOptions) -> tuple[str, object]:
        fields = options.form_fields()
        try:
            with audio_path.open("rb") as handle:
                files = {"file": (audio_path.name, handle, "audio/wav")}
                response = self._client.post(
                    "/v1/audio/transcriptions",
                    headers=self._headers(),
                    data=fields,
                    files=files,
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CrispASRRequestError(
                "CrispASR rejected the transcription request.",
                status_code=exc.response.status_code,
                body=exc.response.text[:2000],
            ) from exc
        except httpx.HTTPError as exc:
            raise CrispASRRequestError("CrispASR transcription request failed.") from exc

        text = response.text
        raw: object = text
        if options.response_format in {"json", "verbose_json"}:
            try:
                raw = response.json()
                text = json.dumps(raw, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                raw = response.text
        return text, raw
