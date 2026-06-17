from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ResponseFormat = Literal["text", "verbose_json", "srt", "vtt", "json"]


@dataclass
class TranscriptionOptions:
    response_format: ResponseFormat = "verbose_json"
    language: str | None = None
    prompt: str | None = None
    vad: bool = False
    diarize: bool = False
    diarize_method: str | None = None
    hotwords: str | None = None
    no_timestamps: bool = False
    extra_fields: dict[str, str] = field(default_factory=dict)

    def form_fields(self) -> dict[str, str]:
        fields: dict[str, str] = {"response_format": self.response_format}
        if self.language:
            fields["language"] = self.language
        if self.prompt:
            fields["prompt"] = self.prompt
        if self.vad:
            fields["vad"] = "true"
        if self.diarize:
            fields["diarize"] = "true"
        if self.diarize_method:
            fields["diarize_method"] = self.diarize_method
        if self.hotwords:
            fields["hotwords"] = self.hotwords
        if self.no_timestamps:
            fields["no_timestamps"] = "true"
        fields.update(self.extra_fields)
        return fields


@dataclass
class HealthStatus:
    status: str | None = None
    backend: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionWindow:
    path: str
    language: str | None
    confidence: float
    decision: str
    raw_output: str = ""


@dataclass
class LanguageDetectionResult:
    decision: Literal["english", "chinese", "uncertain"]
    confidence: float
    detected_language: str | None
    windows: list[DetectionWindow]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MediaInfo:
    kind: Literal["audio", "video", "unknown"]
    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec: str | None = None
    container: str | None = None


@dataclass
class TranscriptionResult:
    text: str
    output_path: Path
    metadata_path: Path
    response_format: ResponseFormat
    profile: str
    backend: str
    server_url: str
    language_detection: LanguageDetectionResult | None = None
    raw_response: Any = None

    def metadata(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "response_format": self.response_format,
            "profile": self.profile,
            "backend": self.backend,
            "server_url": self.server_url,
            "output_path": str(self.output_path),
        }
        if self.language_detection:
            data["language_detection"] = self.language_detection.to_dict()
        return data
