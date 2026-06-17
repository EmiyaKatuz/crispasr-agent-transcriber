from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .errors import BackendMismatchError, TranscriberError

ProfileName = Literal["auto", "english", "chinese"]


@dataclass(frozen=True)
class TranscriptionProfile:
    name: Literal["english", "chinese"]
    backend: str
    default_model: str
    language_hint: str
    description: str

    def server_command(
        self,
        *,
        crispasr_bin: str = "crispasr",
        model: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> list[str]:
        return [
            crispasr_bin,
            "--server",
            "--backend",
            self.backend,
            "-m",
            model or self.default_model,
            "--host",
            host,
            "--port",
            str(port),
        ]


ENGLISH_PROFILE = TranscriptionProfile(
    name="english",
    backend="cohere",
    default_model="auto",
    language_hint="en",
    description="English transcription through Cohere Transcribe 03-2026.",
)

CHINESE_PROFILE = TranscriptionProfile(
    name="chinese",
    backend="qwen3-1.7b",
    default_model="auto",
    language_hint="zh",
    description="Chinese transcription through Qwen3-ASR 1.7B.",
)

PROFILES: dict[str, TranscriptionProfile] = {
    ENGLISH_PROFILE.name: ENGLISH_PROFILE,
    CHINESE_PROFILE.name: CHINESE_PROFILE,
}

ENGLISH_LANG_CODES = {"en", "eng", "en-us", "en-gb", "en-au", "en-nz", "en-ca"}
CHINESE_LANG_CODES = {
    "zh",
    "zho",
    "chi",
    "cmn",
    "yue",
    "wuu",
    "hak",
    "nan",
    "zh-cn",
    "zh-tw",
    "zh-hans",
    "zh-hant",
}


def get_profile(name: str) -> TranscriptionProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise TranscriberError(
            f"Unknown profile '{name}'. Use auto, english, or chinese.",
            code="unknown_profile",
            details={"profile": name},
        ) from exc


def classify_language_code(code: str | None) -> Literal["english", "chinese", "unknown"]:
    if not code:
        return "unknown"
    normalized = code.strip().lower().replace("_", "-")
    if normalized in ENGLISH_LANG_CODES:
        return "english"
    if normalized in CHINESE_LANG_CODES or normalized.startswith("zh-"):
        return "chinese"
    return "unknown"


def validate_backend_for_profile(
    backend: str | None,
    profile: TranscriptionProfile,
    *,
    crispasr_bin: str = "crispasr",
    model: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    if backend == profile.backend:
        return
    command = profile.server_command(
        crispasr_bin=crispasr_bin,
        model=model,
        host=host,
        port=port,
    )
    raise BackendMismatchError(
        "The running CrispASR server is using the wrong backend for this file.",
        expected_backend=profile.backend,
        actual_backend=backend,
        command=command,
    )
