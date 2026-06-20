from __future__ import annotations

import json
from pathlib import Path

from .client import CrispASRClient
from .errors import ServerError
from .language import run_cli_lid
from .media import PreprocessMode, prepare_media
from .profiles import (
    get_profile,
    validate_backend_for_profile,
)
from .schemas import (
    LanguageDetectionResult,
    ResponseFormat,
    TranscriptionOptions,
    TranscriptionResult,
)
from .server_manager import ManagedCrispASRServer

OUTPUT_EXTENSIONS = {
    "text": "txt",
    "verbose_json": "json",
    "json": "json",
    "srt": "srt",
    "vtt": "vtt",
}


def _resolve_model_for_managed_server(
    *,
    model: str | None,
    allow_model_auto_download: bool,
) -> str:
    if model and model != "auto":
        return model
    if allow_model_auto_download:
        return model or "auto"
    raise ServerError(
        "Managed server mode needs a local model path. "
        "Pass --model path\\to\\model.gguf, or use --english-model and "
        "--chinese-model with auto routing. You can also start CrispASR yourself. "
        "Use --allow-model-auto-download only if you want CrispASR to download a model.",
        model=model or "auto",
    )


def _select_model_for_profile(
    *,
    profile_name: str,
    model: str | None,
    english_model: str | None,
    chinese_model: str | None,
) -> str | None:
    if model:
        return model
    if profile_name == "english":
        return english_model
    if profile_name == "chinese":
        return chinese_model
    return None


def _write_outputs(
    *,
    original_path: Path,
    out_dir: Path,
    response_format: ResponseFormat,
    text: str,
    raw_response: object,
    metadata: dict,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    extension = OUTPUT_EXTENSIONS[response_format]
    output_path = out_dir / f"{original_path.stem}.{extension}"
    metadata_path = out_dir / f"{original_path.stem}.metadata.json"
    output_path.write_text(text, encoding="utf-8")
    raw = raw_response if isinstance(raw_response, (dict, list)) else None
    metadata["raw_response"] = raw
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output_path, metadata_path


def _build_server(
    *,
    profile,
    crispasr_bin: str,
    model: str | None,
    host: str,
    port: int,
    keep_server: bool,
) -> tuple[ManagedCrispASRServer, str]:
    server = ManagedCrispASRServer.with_auto_install(
        profile=profile,
        model=model,
        host=host,
        port=port,
        keep_server=keep_server,
    )
    url = server.start()
    return server, url


def run_transcription(
    input_path: str | Path,
    *,
    profile_name: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    out_dir: str | Path = "outputs",
    server_url: str | None = None,
    allow_remote_server: bool = False,
    manage_server: bool = False,
    keep_server: bool = False,
    crispasr_bin: str = "crispasr",
    model: str | None = None,
    english_model: str | None = None,
    chinese_model: str | None = None,
    allow_model_auto_download: bool = False,
    host: str = "127.0.0.1",
    port: int = 8080,
    preprocess: PreprocessMode = "auto",
    language: str | None = None,
    prompt: str | None = None,
    vad: bool = False,
    diarize: bool = False,
    diarize_method: str | None = None,
    hotwords: str | None = None,
    no_timestamps: bool = False,
    api_key: str | None = None,
    lid_backend: str = "firered",
    lid_model: str | None = None,
) -> TranscriptionResult:
    server: ManagedCrispASRServer | None = None
    detection: LanguageDetectionResult | None = None

    with prepare_media(input_path, preprocess=preprocess) as prepared:
        # Language detection (standalone CLI, before server start)
        if profile_name == "auto":
            if not lid_model:
                raise ServerError(
                    "Auto profile needs --lid-model pointing to a local LID model.",
                    lid_backend=lid_backend,
                )
            detection = run_cli_lid(
                prepared.upload_path,
                crispasr_bin=crispasr_bin,
                lid_backend=lid_backend,
                lid_model=lid_model,
            )
            profile = get_profile(detection.decision)
        else:
            profile = get_profile(profile_name)

        selected_model = _select_model_for_profile(
            profile_name=profile.name,
            model=model,
            english_model=english_model,
            chinese_model=chinese_model,
        )
        managed_model = (
            _resolve_model_for_managed_server(
                model=selected_model,
                allow_model_auto_download=allow_model_auto_download,
            )
            if manage_server
            else selected_model
        )

        # Start or connect to server
        active_server_url = server_url
        if active_server_url is None:
            if not manage_server:
                raise ServerError(
                    "No CrispASR server URL was provided. "
                    "Start CrispASR manually or pass --manage-server.",
                    backend=profile.backend,
                    command=profile.server_command(
                        crispasr_bin=crispasr_bin,
                        model=managed_model or "<local-model-path>",
                        host=host,
                        port=port,
                    ),
                )
            server, active_server_url = _build_server(
                profile=profile,
                crispasr_bin=crispasr_bin,
                model=managed_model,
                host=host,
                port=port,
                keep_server=keep_server,
            )

        try:
            with CrispASRClient(
                active_server_url,
                api_key=api_key,
                allow_remote=allow_remote_server,
            ) as client:
                health = client.health()
                validate_backend_for_profile(
                    health.backend,
                    profile,
                    crispasr_bin=crispasr_bin,
                    model=managed_model or "<local-model-path>",
                    host=host,
                    port=port,
                )
                options = TranscriptionOptions(
                    response_format=response_format,
                    language=language or profile.language_hint,
                    prompt=prompt,
                    vad=vad,
                    diarize=diarize,
                    diarize_method=diarize_method,
                    hotwords=hotwords,
                    no_timestamps=no_timestamps,
                )
                text, raw_response = client.transcribe(
                    prepared.upload_path, options
                )
        finally:
            if server and not keep_server:
                server.stop()

        metadata = {
            "original_path": str(prepared.original_path),
            "converted": prepared.converted,
            "media": {
                "kind": prepared.media_info.kind,
                "duration_seconds": prepared.media_info.duration_seconds,
                "sample_rate": prepared.media_info.sample_rate,
                "channels": prepared.media_info.channels,
                "codec": prepared.media_info.codec,
                "container": prepared.media_info.container,
            },
            "profile": profile.name,
            "backend": profile.backend,
            "server_url": active_server_url,
            "language_detection": detection.to_dict() if detection else None,
        }
        output_path, metadata_path = _write_outputs(
            original_path=prepared.original_path,
            out_dir=Path(out_dir),
            response_format=response_format,
            text=text,
            raw_response=raw_response,
            metadata=metadata,
        )
        return TranscriptionResult(
            text=text,
            output_path=output_path,
            metadata_path=metadata_path,
            response_format=response_format,
            profile=profile.name,
            backend=profile.backend,
            server_url=active_server_url,
            language_detection=detection,
            raw_response=raw_response,
        )
