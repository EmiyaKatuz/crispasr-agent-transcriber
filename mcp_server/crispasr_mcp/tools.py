from __future__ import annotations

from pathlib import Path

from crispasr_agent_transcriber.client import CrispASRClient
from crispasr_agent_transcriber.errors import LanguageDetectionError, TranscriberError
from crispasr_agent_transcriber.language import CrispASRLanguageDetector, detect_primary_language
from crispasr_agent_transcriber.media import (
    AUDIO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    create_probe_windows,
    prepare_media,
)
from crispasr_agent_transcriber.schemas import ResponseFormat
from crispasr_agent_transcriber.workflow import run_transcription


def _error_payload(exc: TranscriberError) -> dict:
    return {"ok": False, "error": exc.to_dict()}


def crispasr_health(server_url: str = "http://127.0.0.1:8080") -> dict:
    try:
        with CrispASRClient(server_url) as client:
            health = client.health()
        return {"ok": True, "health": health.raw}
    except TranscriberError as exc:
        return _error_payload(exc)


def crispasr_backends(server_url: str = "http://127.0.0.1:8080") -> dict:
    try:
        with CrispASRClient(server_url) as client:
            return {"ok": True, "backends": client.backends()}
    except TranscriberError as exc:
        return _error_payload(exc)


def crispasr_detect_language(
    file_path: str,
    *,
    crispasr_bin: str = "crispasr",
    lid_backend: str = "silero",
    lid_model: str = "auto",
    allow_model_auto_download: bool = False,
) -> dict:
    try:
        if lid_model == "auto" and not allow_model_auto_download:
            raise LanguageDetectionError(
                "Language detection needs a local LID model path. "
                "Pass lid_model, or set allow_model_auto_download=true.",
                lid_model=lid_model,
            )
        with prepare_media(file_path) as prepared:
            temp_dir, windows = create_probe_windows(
                prepared.upload_path,
                duration_seconds=prepared.media_info.duration_seconds,
            )
            try:
                detector = CrispASRLanguageDetector(
                    crispasr_bin=crispasr_bin,
                    lid_backend=lid_backend,
                    lid_model=lid_model,
                )
                detection = detect_primary_language(windows, detector)
            finally:
                temp_dir.cleanup()
        return {"ok": True, "language_detection": detection.to_dict()}
    except TranscriberError as exc:
        return _error_payload(exc)


def transcribe_audio(
    file_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
) -> dict:
    try:
        result = run_transcription(
            file_path,
            profile_name=profile,
            response_format=response_format,
            out_dir=out_dir,
            server_url=server_url,
            manage_server=manage_server,
            model=model,
            allow_model_auto_download=allow_model_auto_download,
        )
        return {"ok": True, "result": result.metadata()}
    except TranscriberError as exc:
        return _error_payload(exc)


def transcribe_video(
    file_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
) -> dict:
    return transcribe_audio(
        file_path,
        profile=profile,
        response_format=response_format,
        out_dir=out_dir,
        server_url=server_url,
        manage_server=manage_server,
        model=model,
        allow_model_auto_download=allow_model_auto_download,
    )


def transcribe_folder(
    folder_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
) -> dict:
    folder = Path(folder_path).expanduser().resolve()
    if not folder.is_dir():
        return {"ok": False, "error": {"code": "invalid_folder", "message": "Folder not found."}}

    supported = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
    results = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in supported:
            continue
        results.append(
            transcribe_audio(
                str(path),
                profile=profile,
                response_format=response_format,
                out_dir=out_dir,
                server_url=server_url,
                manage_server=manage_server,
                model=model,
                allow_model_auto_download=allow_model_auto_download,
            )
        )
    return {"ok": True, "results": results}
