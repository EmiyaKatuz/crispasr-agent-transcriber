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
from crispasr_agent_transcriber.models import (
    download_models,
    list_model_options,
    resolve_recommended_model_paths,
)
from crispasr_agent_transcriber.schemas import ResponseFormat
from crispasr_agent_transcriber.video_understanding import run_video_understanding
from crispasr_agent_transcriber.workflow import run_transcription


def _error_payload(exc: Exception) -> dict:
    if isinstance(exc, TranscriberError):
        return {"ok": False, "error": exc.to_dict()}
    return {"ok": False, "error": {"code": "internal_error", "message": str(exc)}}


def _installed_default(path: str | None) -> str | None:
    if path and Path(path).is_file():
        return path
    return None


def _merge_model_defaults(
    *,
    models_dir: str,
    english_model: str | None,
    chinese_model: str | None,
    lid_model: str | None,
) -> tuple[str | None, str | None, str | None]:
    defaults = resolve_recommended_model_paths(models_dir)
    return (
        english_model or _installed_default(defaults["english_model"]),
        chinese_model or _installed_default(defaults["chinese_model"]),
        lid_model or _installed_default(defaults["lid_model"]),
    )


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


def crispasr_list_models(models_dir: str = "models") -> dict:
    """List approved local GGUF model choices and installation status."""
    try:
        return {"ok": True, **list_model_options(models_dir)}
    except Exception as exc:
        return _error_payload(exc)


def crispasr_download_models(
    model_ids: list[str] | None = None,
    *,
    models_dir: str = "models",
    overwrite: bool = False,
) -> dict:
    """Download approved GGUF models into a local models directory.

    Downloads only from the built-in allowlist. By default, installs the
    recommended English, Chinese, and language-detection models.
    """
    try:
        return {
            "ok": True,
            **download_models(model_ids, models_dir=models_dir, overwrite=overwrite),
        }
    except Exception as exc:
        return _error_payload(exc)


def crispasr_resolve_model_paths(models_dir: str = "models") -> dict:
    """Return recommended local model paths for auto-routed transcription."""
    try:
        return {"ok": True, **resolve_recommended_model_paths(models_dir)}
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
    english_model: str | None = None,
    chinese_model: str | None = None,
    models_dir: str = "models",
    allow_model_auto_download: bool = False,
    lid_backend: str = "firered",
    lid_model: str | None = None,
) -> dict:
    """Transcribe a local audio file through a CrispASR server.

    Supports auto language routing (needs --lid-model) or explicit
    english / chinese profiles. Can start a managed server on demand.
    """
    try:
        english_model, chinese_model, lid_model = _merge_model_defaults(
            models_dir=models_dir,
            english_model=english_model,
            chinese_model=chinese_model,
            lid_model=lid_model,
        )
        result = run_transcription(
            file_path,
            profile_name=profile,
            response_format=response_format,
            out_dir=out_dir,
            server_url=server_url,
            manage_server=manage_server,
            keep_server=keep_server,
            model=model,
            english_model=english_model,
            chinese_model=chinese_model,
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
    english_model: str | None = None,
    chinese_model: str | None = None,
    models_dir: str = "models",
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
        english_model=english_model,
        chinese_model=chinese_model,
        models_dir=models_dir,
        allow_model_auto_download=allow_model_auto_download,
        lid_backend=lid_backend,
        lid_model=lid_model,
    )


def understand_video(
    file_path: str,
    *,
    profile: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str = "outputs",
    server_url: str | None = None,
    manage_server: bool = False,
    keep_server: bool = False,
    model: str | None = None,
    english_model: str | None = None,
    chinese_model: str | None = None,
    models_dir: str = "models",
    allow_model_auto_download: bool = False,
    lid_backend: str = "firered",
    lid_model: str | None = None,
    keyframe_interval_seconds: float = 30.0,
    max_keyframes: int = 12,
    max_return_text_chars: int = 4000,
    ffmpeg_bin: str = "ffmpeg",
) -> dict:
    """Transcribe a local video, capture synced keyframes, and persist an agent context."""
    try:
        english_model, chinese_model, lid_model = _merge_model_defaults(
            models_dir=models_dir,
            english_model=english_model,
            chinese_model=chinese_model,
            lid_model=lid_model,
        )
        result = run_video_understanding(
            file_path,
            profile_name=profile,
            response_format=response_format,
            out_dir=out_dir,
            server_url=server_url,
            manage_server=manage_server,
            keep_server=keep_server,
            model=model,
            english_model=english_model,
            chinese_model=chinese_model,
            allow_model_auto_download=allow_model_auto_download,
            lid_backend=lid_backend,
            lid_model=lid_model,
            keyframe_interval_seconds=keyframe_interval_seconds,
            max_keyframes=max_keyframes,
            max_return_text_chars=max_return_text_chars,
            ffmpeg_bin=ffmpeg_bin,
        )
        return {
            "ok": True,
            "manifest_path": str(result.manifest_path),
            "agent_context_path": str(result.agent_context_path),
            "transcript_path": str(result.transcript_path),
            "metadata_path": str(result.metadata_path),
            "keyframes": result.keyframes,
            "agent_payload": result.agent_payload,
        }
    except Exception as exc:
        return _error_payload(exc)


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
    english_model: str | None = None,
    chinese_model: str | None = None,
    models_dir: str = "models",
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
                    english_model=english_model,
                    chinese_model=chinese_model,
                    models_dir=models_dir,
                    allow_model_auto_download=allow_model_auto_download,
                    lid_backend=lid_backend,
                    lid_model=lid_model,
                )
            )
        return {"ok": True, "results": results}
    except Exception as exc:
        return _error_payload(exc)
