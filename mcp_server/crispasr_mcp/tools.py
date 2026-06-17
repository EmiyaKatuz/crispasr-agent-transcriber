from __future__ import annotations

from pathlib import Path

from crispasr_agent_transcriber.client import CrispASRClient
from crispasr_agent_transcriber.errors import TranscriberError
from crispasr_agent_transcriber.language import run_cli_lid
from crispasr_agent_transcriber.media import (
    AUDIO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    prepare_media,
)
from crispasr_agent_transcriber.schemas import ResponseFormat
from crispasr_agent_transcriber.workflow import run_transcription


def _error_payload(exc: Exception) -> dict:
    if isinstance(exc, TranscriberError):
        return {"ok": False, "error": exc.to_dict()}
    return {"ok": False, "error": {"code": "internal_error", "message": str(exc)}}


def crispasr_health(server_url: str = "http://127.0.0.1:8080") -> dict:
    """Check whether a CrispASR server is running and what backend it uses."""
    try:
        with CrispASRClient(server_url) as client:
            health = client.health()
        return {"ok": True, "health": health.raw}
    except Exception as exc:
        return _error_payload(exc)


def crispasr_backends(server_url: str = "http://127.0.0.1:8080") -> dict:
    """List available backends from a running CrispASR server."""
    try:
        with CrispASRClient(server_url) as client:
            return {"ok": True, "backends": client.backends()}
    except Exception as exc:
        return _error_payload(exc)


def crispasr_detect_language(
    file_path: str,
    *,
    crispasr_bin: str = "crispasr",
    lid_backend: str = "firered",
    lid_model: str,
) -> dict:
    """Run language detection on a media file using CrispASR LID.

    Returns the detected language and routing decision (english / chinese / uncertain).
    Requires a local LID model path. The firered backend is recommended.
    """
    try:
        with prepare_media(file_path) as prepared:
            detection = run_cli_lid(
                prepared.upload_path,
                crispasr_bin=crispasr_bin,
                lid_backend=lid_backend,
                lid_model=lid_model,
            )
        return {"ok": True, "language_detection": detection.to_dict()}
    except Exception as exc:
        return _error_payload(exc)


def transcribe_audio(
    file_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    keep_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
    lid_backend: str = "firered",
    lid_model: str | None = None,
) -> dict:
    """Transcribe a local audio file through a CrispASR server.

    Supports auto language routing (needs --lid-model) or explicit
    english / chinese profiles. Can start a managed server on demand.
    """
    try:
        result = run_transcription(
            file_path,
            profile_name=profile,
            response_format=response_format,
            out_dir=out_dir,
            server_url=server_url,
            manage_server=manage_server,
            keep_server=keep_server,
            model=model,
            allow_model_auto_download=allow_model_auto_download,
            lid_backend=lid_backend,
            lid_model=lid_model,
        )
        return {
            "ok": True,
            "text": result.text,
            "output_path": str(result.output_path),
            "metadata_path": str(result.metadata_path),
            "profile": result.profile,
            "backend": result.backend,
        }
    except Exception as exc:
        return _error_payload(exc)


def transcribe_video(
    file_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    keep_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
    lid_backend: str = "firered",
    lid_model: str | None = None,
) -> dict:
    """Transcribe a local video file through a CrispASR server.

    Extracts audio with ffmpeg before sending to CrispASR.
    Supports the same options as transcribe_audio.
    """
    return transcribe_audio(
        file_path,
        profile=profile,
        response_format=response_format,
        out_dir=out_dir,
        server_url=server_url,
        manage_server=manage_server,
        keep_server=keep_server,
        model=model,
        allow_model_auto_download=allow_model_auto_download,
        lid_backend=lid_backend,
        lid_model=lid_model,
    )


def transcribe_folder(
    folder_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    keep_server: bool = False,
    model: str | None = None,
    allow_model_auto_download: bool = False,
    lid_backend: str = "firered",
    lid_model: str | None = None,
) -> dict:
    """Batch-transcribe all supported media files in a folder.

    Keeps a managed server running across all files when --manage-server
    and --keep-server are both set.
    """
    try:
        folder = Path(folder_path).expanduser().resolve()
        if not folder.is_dir():
            return {
                "ok": False,
                "error": {
                    "code": "invalid_folder",
                    "message": "Folder not found.",
                },
            }

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
                    keep_server=keep_server,
                    model=model,
                    allow_model_auto_download=allow_model_auto_download,
                    lid_backend=lid_backend,
                    lid_model=lid_model,
                )
            )
        return {"ok": True, "results": results}
    except Exception as exc:
        return _error_payload(exc)