from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .crispasr_manager import (
    BIN_DIR as DEFAULT_BIN_DIR,
)
from .crispasr_manager import (
    check_for_update,
    find_binary,
)
from .errors import TranscriberError
from .models import download_models, list_model_options, resolve_recommended_model_paths
from .workflow import run_transcription


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe local audio or video through a local CrispASR server."
    )
    parser.add_argument("input", nargs="?", help="Local audio or video file to transcribe.")
    parser.add_argument(
        "--profile",
        choices=["auto", "english", "chinese"],
        default="auto",
        help="Route automatically, or force the English/Cohere or Chinese/Qwen3-1.7B path.",
    )
    parser.add_argument(
        "--format",
        dest="response_format",
        choices=["text", "verbose_json", "srt", "vtt", "json"],
        default="verbose_json",
        help="Transcript output format.",
    )
    parser.add_argument("--out-dir", default="outputs", help="Directory for transcript outputs.")
    parser.add_argument("--server-url", help="Existing local CrispASR server URL.")
    parser.add_argument(
        "--allow-remote-server",
        action="store_true",
        help="Allow non-localhost CrispASR server URLs. Use only for trusted servers.",
    )
    parser.add_argument(
        "--manage-server",
        action="store_true",
        help="Start one local CrispASR server after profile selection.",
    )
    parser.add_argument(
        "--keep-server",
        action="store_true",
        help="Leave a managed CrispASR server running after transcription.",
    )
    parser.add_argument(
        "--crispasr-bin-dir",
        default=os.environ.get("CRISPASR_BIN_DIR", str(DEFAULT_BIN_DIR)),
        help="Directory containing the crispasr executable.",
    )
    parser.add_argument(
        "--crispasr-bin",
        default=None,
        help="Explicit path to crispasr executable (overrides bin dir).",
    )
    parser.add_argument(
        "--model",
        help="Local GGUF model path override for managed server mode.",
    )
    parser.add_argument(
        "--english-model",
        help="Local Cohere GGUF path selected when the resolved profile is English.",
    )
    parser.add_argument(
        "--chinese-model",
        help="Local Qwen3-ASR GGUF path selected when the resolved profile is Chinese.",
    )
    parser.add_argument(
        "--allow-model-auto-download",
        action="store_true",
        help="Allow managed server mode to pass -m auto to CrispASR.",
    )
    parser.add_argument(
        "--models-dir",
        default=os.environ.get("CRISPASR_MODELS_DIR", "models"),
        help="Directory containing approved local GGUF models.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Managed server host.")
    parser.add_argument("--port", type=int, default=8080, help="Managed server port.")
    parser.add_argument(
        "--preprocess",
        choices=["auto", "always", "never"],
        default="auto",
        help="Whether to convert media to mono 16 kHz WAV before upload.",
    )
    parser.add_argument("--language", help="Language hint passed to CrispASR transcription.")
    parser.add_argument("--prompt", help="Initial prompt/context passed to CrispASR.")
    parser.add_argument("--vad", action="store_true", help="Enable CrispASR VAD.")
    parser.add_argument("--diarize", action="store_true", help="Enable CrispASR diarization.")
    parser.add_argument("--diarize-method", help="CrispASR diarization method.")
    parser.add_argument("--hotwords", help="Comma-separated hotwords.")
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Ask CrispASR to omit timestamps when supported.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CRISPASR_API_KEY"),
        help="CrispASR API key, if CRISPASR_API_KEYS is enabled.",
    )
    parser.add_argument("--lid-backend", default="firered",
        help="CrispASR audio-LID backend (firered, whisper, silero).")
    parser.add_argument("--lid-model", default=None,
        help="Local LID model path (required for --profile auto).")

    setup_group = parser.add_argument_group("CrispASR setup")
    setup_group.add_argument(
        "--install-crispasr",
        action="store_true",
        help="Download and install the latest CrispASR binary.",
    )
    setup_group.add_argument(
        "--update-crispasr",
        action="store_true",
        help="Check for and install a newer CrispASR release.",
    )
    setup_group.add_argument(
        "--crispasr-status",
        action="store_true",
        help="Show installed CrispASR version and check for updates.",
    )
    setup_group.add_argument(
        "--list-models",
        action="store_true",
        help="List approved GGUF models and show which recommended files are installed.",
    )
    setup_group.add_argument(
        "--download-models",
        action="store_true",
        help="Download the recommended English, Chinese, and LID GGUF models.",
    )
    setup_group.add_argument(
        "--model-id",
        action="append",
        dest="model_ids",
        help="With --download-models, download this model id instead of the default bundle.",
    )
    setup_group.add_argument(
        "--overwrite-models",
        action="store_true",
        help="Replace existing model files when used with --download-models.",
    )
    return parser


def _resolve_crispasr_bin(args: argparse.Namespace) -> str:
    if args.crispasr_bin:
        return args.crispasr_bin
    bin_dir = Path(args.crispasr_bin_dir)
    binary = find_binary(bin_dir=bin_dir)
    if binary:
        return str(binary)
    return "crispasr"


def _handle_setup_command(args: argparse.Namespace) -> int:
    bin_dir = Path(args.crispasr_bin_dir)

    if args.list_models:
        options = list_model_options(args.models_dir)
        print(f"Models directory: {options['models_dir']}")
        print(f"Recommended bundle ready: {'yes' if options['ready'] else 'no'}")
        for model in options["models"]:
            marker = "*" if model["recommended"] else "-"
            state = "installed" if model["installed"] else "missing"
            print(f"{marker} {model['id']} ({model['purpose']}, {model['quantization']}): {state}")
            print(f"  file: {model['path']}")
            print(f"  source: {model['source_url']}")
        return 0

    if args.download_models:
        result = download_models(
            args.model_ids,
            models_dir=args.models_dir,
            overwrite=args.overwrite_models,
        )
        print(f"Models directory: {result['models_dir']}")
        for item in result["results"]:
            action = "downloaded" if item["downloaded"] else "skipped"
            print(f"{action}: {item['id']} -> {item['path']}")
        print(f"Recommended bundle ready: {'yes' if result['ready'] else 'no'}")
        return 0

    if args.crispasr_status:
        current = find_binary(bin_dir=bin_dir)
        if current:
            ver = "installed"
            try:
                from .crispasr_manager import installed_version
                ver = installed_version(bin_dir=bin_dir) or ver
            except Exception:
                pass
            print(f"CrispASR: {current} ({ver})")
            update_info = check_for_update(bin_dir=bin_dir)
            if update_info:
                print(f"Update available: {update_info.version}")
                print("Run with --update-crispasr to upgrade.")
            else:
                print("Up to date.")
        else:
            print("CrispASR not installed.")
            print("Run with --install-crispasr to download it.")
        return 0

    if args.update_crispasr:
        from .crispasr_manager import update as do_update
        path = do_update(bin_dir=bin_dir)
        print(f"CrispASR updated: {path}")
        return 0

    if args.install_crispasr:
        from .crispasr_manager import install as do_install
        path = do_install(bin_dir=bin_dir)
        print(f"CrispASR installed: {path}")
        return 0

    return -1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_rc = _handle_setup_command(args)
    if setup_rc != -1:
        return setup_rc

    if not args.input:
        parser.print_help()
        return 1

    try:
        crispasr_bin = _resolve_crispasr_bin(args)
        model_defaults = resolve_recommended_model_paths(args.models_dir)
        default_english_model = (
            model_defaults["english_model"]
            if model_defaults["english_model"] and Path(model_defaults["english_model"]).is_file()
            else None
        )
        default_chinese_model = (
            model_defaults["chinese_model"]
            if model_defaults["chinese_model"] and Path(model_defaults["chinese_model"]).is_file()
            else None
        )
        default_lid_model = (
            model_defaults["lid_model"]
            if model_defaults["lid_model"] and Path(model_defaults["lid_model"]).is_file()
            else None
        )
        result = run_transcription(
            Path(args.input),
            profile_name=args.profile,
            response_format=args.response_format,
            out_dir=args.out_dir,
            server_url=args.server_url,
            allow_remote_server=args.allow_remote_server,
            manage_server=args.manage_server,
            keep_server=args.keep_server,
            crispasr_bin=crispasr_bin,
            model=args.model,
            english_model=args.english_model or default_english_model,
            chinese_model=args.chinese_model or default_chinese_model,
            allow_model_auto_download=args.allow_model_auto_download,
            host=args.host,
            port=args.port,
            preprocess=args.preprocess,
            language=args.language,
            prompt=args.prompt,
            vad=args.vad,
            diarize=args.diarize,
            diarize_method=args.diarize_method,
            hotwords=args.hotwords,
            no_timestamps=args.no_timestamps,
            api_key=args.api_key,
            lid_backend=args.lid_backend,
            lid_model=args.lid_model or default_lid_model,
        )
    except TranscriberError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    print(f"Transcript: {result.output_path}")
    print(f"Metadata:  {result.metadata_path}")
    print(f"Profile:   {result.profile} ({result.backend})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
