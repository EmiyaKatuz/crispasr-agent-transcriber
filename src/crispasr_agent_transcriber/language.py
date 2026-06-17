from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .errors import LanguageDetectionError, UncertainLanguageError
from .schemas import DetectionWindow, LanguageDetectionResult


def _resolve_lid_backend_name(lid_backend: str) -> str:
    """Map user-friendly backend names to CrispASR --backend values."""
    mapping = {
        "silero": "lid-silero",
        "ecapa": "lid-ecapa",
        "firered": "firered",
        "whisper": "whisper",
    }
    return mapping.get(lid_backend, lid_backend)


def run_cli_lid(
    audio_path: str | Path,
    *,
    crispasr_bin: str = "crispasr",
    lid_backend: str = "firered",
    lid_model: str,
    timeout_seconds: float = 120.0,
) -> LanguageDetectionResult:
    """Run language detection via standalone CrispASR CLI."""
    backend = _resolve_lid_backend_name(lid_backend)
    command = [
        crispasr_bin,
        "--backend", backend,
        "-m", lid_model,
        "-f", str(audio_path),
        "--detect-language",
        "--no-prints",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise LanguageDetectionError(
            "CrispASR binary was not found for language detection.",
            command=command,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise LanguageDetectionError(
            "CrispASR language detection timed out.",
            command=command,
            timeout_seconds=timeout_seconds,
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise LanguageDetectionError(
            "CrispASR language detection failed.",
            command=command,
            stderr=exc.stderr[-1000:],
            stdout=exc.stdout[-1000:],
        ) from exc

    raw = "\n".join(
        part for part in [completed.stdout, completed.stderr] if part
    )
    detected = _parse_lid_output(raw)
    decision = _classify(detected)
    window = DetectionWindow(
        path=str(audio_path),
        language=detected,
        confidence=1.0,
        decision=decision,
    )
    detection = LanguageDetectionResult(
        decision=decision,
        confidence=1.0,
        detected_language=detected,
        windows=[window],
    )
    if decision == "uncertain":
        raise UncertainLanguageError(
            "The main spoken language was not clearly English or Chinese. "
            "Rerun with --profile english or --profile chinese.",
            detection=detection.to_dict(),
        )
    return detection


def _parse_lid_output(raw: str) -> str | None:
    """Extract ISO language code from CrispASR LID output."""
    for line in reversed(raw.strip().splitlines()):
        line = line.strip()
        # CrispASR sometimes appends punctuation (e.g. "Zh?" or "en.")
        cleaned = re.sub(r"[^a-zA-Z_-]", "", line)
        if re.match(r"^[a-zA-Z]{2,3}$", cleaned):
            return cleaned.lower()
        if re.match(r"^[a-zA-Z]{2,3}[-_][A-Za-z]+$", cleaned):
            return cleaned.split("-")[0].split("_")[0].lower()
        # Handle "Zh?" / "En?" format directly
        if re.match(r"^[A-Z][a-z]+\?$", line.strip()):
            return line.strip().rstrip("?").lower()
    return None


ENGLISH_CODES = {"en", "eng", "en-us", "en-gb", "en-au", "en-nz", "en-ca"}
CHINESE_CODES = {
    "zh", "zho", "chi", "cmn", "yue", "wuu", "hak", "nan",
    "zh-cn", "zh-tw", "zh-hans", "zh-hant",
}


def _classify(code: str | None) -> str:
    if not code:
        return "uncertain"
    normalized = code.strip().lower().replace("_", "-")
    if normalized in ENGLISH_CODES:
        return "english"
    if normalized in CHINESE_CODES or normalized.startswith("zh-"):
        return "chinese"
    return "uncertain"