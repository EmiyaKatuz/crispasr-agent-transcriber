from __future__ import annotations

import json
import os
import shutil
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .errors import TranscriberError

ModelRole = Literal["english", "chinese", "lid"]

MODEL_MANIFEST = "model-manifest.json"
HUGGING_FACE_BASE = "https://huggingface.co"


@dataclass(frozen=True)
class ModelSpec:
    id: str
    role: ModelRole
    purpose: str
    repo: str
    filename: str
    quantization: str
    recommended: bool
    description: str

    @property
    def source_url(self) -> str:
        return f"{HUGGING_FACE_BASE}/{self.repo}"

    @property
    def download_url(self) -> str:
        return f"{self.source_url}/resolve/main/{self.filename}"

    def to_dict(self, *, models_dir: Path | None = None) -> dict:
        data = asdict(self)
        data["source_url"] = self.source_url
        data["download_url"] = self.download_url
        if models_dir is not None:
            path = models_dir / self.filename
            data["path"] = str(path)
            data["installed"] = path.is_file()
        return data


MODEL_CATALOG: tuple[ModelSpec, ...] = (
    ModelSpec(
        id="english-q4",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe-q4_k.gguf",
        quantization="q4_k",
        recommended=True,
        description="Default English model with lower disk and memory use.",
    ),
    ModelSpec(
        id="english-q5-0",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe-q5_0.gguf",
        quantization="q5_0",
        recommended=False,
        description="Higher quality English option than q4_k.",
    ),
    ModelSpec(
        id="english-q5-1",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe-q5_1.gguf",
        quantization="q5_1",
        recommended=False,
        description="Alternate q5 English quantization.",
    ),
    ModelSpec(
        id="english-q6",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe-q6_k.gguf",
        quantization="q6_k",
        recommended=False,
        description="Larger English model for quality-focused local use.",
    ),
    ModelSpec(
        id="english-q8",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe-q8_0.gguf",
        quantization="q8_0",
        recommended=False,
        description="Large English model with less quantization.",
    ),
    ModelSpec(
        id="english-f16",
        role="english",
        purpose="English transcription",
        repo="cstr/cohere-transcribe-03-2026-GGUF",
        filename="cohere-transcribe.gguf",
        quantization="f16",
        recommended=False,
        description="Largest English option from the upstream GGUF repo.",
    ),
    ModelSpec(
        id="chinese-q4",
        role="chinese",
        purpose="Chinese transcription",
        repo="cstr/qwen3-asr-1.7b-GGUF",
        filename="qwen3-asr-1.7b-q4_k.gguf",
        quantization="q4_k",
        recommended=True,
        description="Default Chinese model with practical disk and memory use.",
    ),
    ModelSpec(
        id="chinese-q8",
        role="chinese",
        purpose="Chinese transcription",
        repo="cstr/qwen3-asr-1.7b-GGUF",
        filename="qwen3-asr-1.7b-q8_0.gguf",
        quantization="q8_0",
        recommended=False,
        description="Larger Chinese model with less quantization.",
    ),
    ModelSpec(
        id="chinese-f16",
        role="chinese",
        purpose="Chinese transcription",
        repo="cstr/qwen3-asr-1.7b-GGUF",
        filename="qwen3-asr-1.7b-f16.gguf",
        quantization="f16",
        recommended=False,
        description="Largest Chinese option from the upstream GGUF repo.",
    ),
    ModelSpec(
        id="lid-q2",
        role="lid",
        purpose="English/Chinese language detection",
        repo="cstr/firered-lid-GGUF",
        filename="firered-lid-q2_k.gguf",
        quantization="q2_k",
        recommended=False,
        description="Smallest local language-detection option.",
    ),
    ModelSpec(
        id="lid-q4",
        role="lid",
        purpose="English/Chinese language detection",
        repo="cstr/firered-lid-GGUF",
        filename="firered-lid-q4_k.gguf",
        quantization="q4_k",
        recommended=True,
        description="Default local language-detection model.",
    ),
    ModelSpec(
        id="lid-q8",
        role="lid",
        purpose="English/Chinese language detection",
        repo="cstr/firered-lid-GGUF",
        filename="firered-lid-q8_0.gguf",
        quantization="q8_0",
        recommended=False,
        description="Larger language-detection option with less quantization.",
    ),
    ModelSpec(
        id="lid-f16",
        role="lid",
        purpose="English/Chinese language detection",
        repo="cstr/firered-lid-GGUF",
        filename="firered-lid-f16.gguf",
        quantization="f16",
        recommended=False,
        description="Largest language-detection option from the upstream GGUF repo.",
    ),
)


def _reject_urlish_path(value: str | Path) -> None:
    raw = str(value)
    lowered = raw.lower()
    if "\x00" in raw:
        raise TranscriberError(
            "Model directory contains an invalid NUL byte.",
            code="invalid_model_dir",
        )
    if "://" in raw or lowered.startswith(("http:", "https:", "ftp:", "s3:", "gs:", "file:")):
        raise TranscriberError(
            "Only local filesystem paths are accepted for model storage.",
            code="invalid_model_dir",
            details={"path": raw},
        )


def resolve_models_dir(models_dir: str | Path = "models") -> Path:
    _reject_urlish_path(models_dir)
    resolved = Path(models_dir).expanduser().resolve()
    if resolved == resolved.anchor or resolved == Path.home().resolve():
        raise TranscriberError(
            "Refusing to use a filesystem root or home directory as the model directory.",
            code="unsafe_model_dir",
            details={"path": str(resolved)},
        )
    return resolved


def get_model_spec(model_id: str) -> ModelSpec:
    normalized = model_id.strip().lower()
    for model in MODEL_CATALOG:
        if normalized in {model.id, model.filename.lower()}:
            return model
    raise TranscriberError(
        "Unknown CrispASR model id.",
        code="unknown_model",
        details={"model_id": model_id, "known_ids": [model.id for model in MODEL_CATALOG]},
    )


def recommended_model_ids() -> list[str]:
    return [model.id for model in MODEL_CATALOG if model.recommended]


def list_model_options(models_dir: str | Path = "models") -> dict:
    resolved = resolve_models_dir(models_dir)
    models = [model.to_dict(models_dir=resolved) for model in MODEL_CATALOG]
    recommended = [model for model in models if model["recommended"]]
    return {
        "models_dir": str(resolved),
        "models": models,
        "recommended_model_ids": recommended_model_ids(),
        "recommended_paths": {
            model["role"]: model["path"] for model in recommended
        },
        "ready": all(model["installed"] for model in recommended),
        "missing_recommended": [model for model in recommended if not model["installed"]],
    }


def resolve_recommended_model_paths(models_dir: str | Path = "models") -> dict:
    options = list_model_options(models_dir)
    return {
        "models_dir": options["models_dir"],
        "ready": options["ready"],
        "english_model": options["recommended_paths"].get("english"),
        "chinese_model": options["recommended_paths"].get("chinese"),
        "lid_model": options["recommended_paths"].get("lid"),
        "missing_recommended": options["missing_recommended"],
    }


def _read_manifest(models_dir: Path) -> dict:
    manifest_path = models_dir / MODEL_MANIFEST
    if not manifest_path.is_file():
        return {"models": []}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"models": []}


def _write_manifest(models_dir: Path, entries: list[dict]) -> Path:
    manifest = _read_manifest(models_dir)
    current = {
        item.get("id"): item
        for item in manifest.get("models", [])
        if isinstance(item, dict) and item.get("id")
    }
    for entry in entries:
        current[entry["id"]] = entry
    manifest = {
        "updated_at": datetime.now(UTC).isoformat(),
        "models": sorted(current.values(), key=lambda item: item["id"]),
    }
    manifest_path = models_dir / MODEL_MANIFEST
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def download_model(
    model_id: str,
    *,
    models_dir: str | Path = "models",
    overwrite: bool = False,
    timeout_seconds: int = 60,
) -> dict:
    spec = get_model_spec(model_id)
    resolved_dir = resolve_models_dir(models_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    destination = resolved_dir / spec.filename

    if destination.exists() and not overwrite:
        return {
            "id": spec.id,
            "filename": spec.filename,
            "path": str(destination),
            "downloaded": False,
            "skipped": True,
            "reason": "already_exists",
            "source_url": spec.source_url,
        }

    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        request = urllib.request.Request(
            spec.download_url,
            headers={"User-Agent": "crispasr-agent-transcriber"},
        )
        with (
            urllib.request.urlopen(request, timeout=timeout_seconds) as response,
            partial.open("wb") as handle,
        ):
            shutil.copyfileobj(response, handle)
        os.replace(partial, destination)
    except (OSError, urllib.error.URLError) as exc:
        partial.unlink(missing_ok=True)
        raise TranscriberError(
            "Failed to download CrispASR model.",
            code="model_download_failed",
            details={"model_id": spec.id, "url": spec.download_url, "error": str(exc)},
        ) from exc

    entry = {
        "id": spec.id,
        "role": spec.role,
        "filename": spec.filename,
        "path": str(destination),
        "source_url": spec.source_url,
        "download_url": spec.download_url,
        "downloaded_at": datetime.now(UTC).isoformat(),
        "size_bytes": destination.stat().st_size,
    }
    manifest_path = _write_manifest(resolved_dir, [entry])
    return {
        **entry,
        "downloaded": True,
        "skipped": False,
        "manifest_path": str(manifest_path),
    }


def download_models(
    model_ids: list[str] | None = None,
    *,
    models_dir: str | Path = "models",
    overwrite: bool = False,
    timeout_seconds: int = 60,
) -> dict:
    selected_ids = model_ids or recommended_model_ids()
    results = [
        download_model(
            model_id,
            models_dir=models_dir,
            overwrite=overwrite,
            timeout_seconds=timeout_seconds,
        )
        for model_id in selected_ids
    ]
    paths = resolve_recommended_model_paths(models_dir)
    return {
        "models_dir": paths["models_dir"],
        "requested_model_ids": selected_ids,
        "results": results,
        "ready": paths["ready"],
        "recommended_paths": {
            "english_model": paths["english_model"],
            "chinese_model": paths["chinese_model"],
            "lid_model": paths["lid_model"],
        },
        "missing_recommended": paths["missing_recommended"],
    }
