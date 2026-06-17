from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .errors import LanguageDetectionError, UncertainLanguageError
from .profiles import classify_language_code
from .schemas import DetectionWindow, LanguageDetectionResult


@dataclass(frozen=True)
class WindowLanguage:
    language: str | None
    confidence: float
    raw_output: str


class LanguageDetector(Protocol):
    def detect(self, audio_path: Path) -> WindowLanguage:
        ...


class CrispASRLanguageDetector:
    """Runs local CrispASR audio language detection for short probe files."""

    def __init__(
        self,
        *,
        crispasr_bin: str = "crispasr",
        lid_backend: str = "silero",
        lid_model: str = "auto",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.crispasr_bin = crispasr_bin
        self.lid_backend = lid_backend
        self.lid_model = lid_model
        self.timeout_seconds = timeout_seconds

    def command(self, audio_path: Path) -> list[str]:
        backend = self.lid_backend
        if backend == "silero":
            backend = "lid-silero"
        elif backend == "ecapa":
            backend = "lid-ecapa"
        elif backend == "firered":
            backend = "lid-firered"
        return [
            self.crispasr_bin,
            "--backend",
            backend,
            "-m",
            self.lid_model,
            "-f",
            str(audio_path),
            "--detect-language",
            "--no-prints",
        ]

    def detect(self, audio_path: Path) -> WindowLanguage:
        command = self.command(audio_path)
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise LanguageDetectionError(
                "CrispASR binary was not found for local language detection.",
                command=command,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise LanguageDetectionError(
                "CrispASR language detection timed out.",
                command=command,
                timeout_seconds=self.timeout_seconds,
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise LanguageDetectionError(
                "CrispASR language detection failed.",
                command=command,
                stderr=exc.stderr[-1000:],
                stdout=exc.stdout[-1000:],
            ) from exc

        raw_output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
        return parse_language_output(raw_output)


def parse_language_output(raw_output: str) -> WindowLanguage:
    stripped = raw_output.strip()
    if not stripped:
        return WindowLanguage(language=None, confidence=0.0, raw_output=raw_output)

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            language = parsed.get("language") or parsed.get("lang") or parsed.get("lang_code")
            confidence = parsed.get("confidence") or parsed.get("probability") or parsed.get("prob")
            return WindowLanguage(
                language=str(language) if language else None,
                confidence=float(confidence) if confidence is not None else 0.0,
                raw_output=raw_output,
            )
    except json.JSONDecodeError:
        pass

    tab_match = re.search(r"\b([a-z]{2,3}(?:[-_][A-Za-z]+)?)\s+([01](?:\.\d+)?)\b", stripped)
    if tab_match:
        return WindowLanguage(
            language=tab_match.group(1),
            confidence=float(tab_match.group(2)),
            raw_output=raw_output,
        )

    lang_match = re.search(
        r"\b(?:lang|language|detected_language)\b\s*[:=]\s*['\"]?([a-z]{2,3}(?:[-_][A-Za-z]+)?)",
        stripped,
        re.IGNORECASE,
    )
    confidence_match = re.search(
        r"\b(?:confidence|conf|probability|prob|p)\b\s*[:=]\s*([01](?:\.\d+)?)",
        stripped,
        re.IGNORECASE,
    )
    return WindowLanguage(
        language=lang_match.group(1) if lang_match else None,
        confidence=float(confidence_match.group(1)) if confidence_match else 0.0,
        raw_output=raw_output,
    )


def aggregate_language_results(
    window_results: list[WindowLanguage],
    *,
    min_confidence: float = 0.45,
    min_share: float = 0.6,
    min_margin: float = 0.2,
) -> LanguageDetectionResult:
    windows: list[DetectionWindow] = []
    scores = {"english": 0.0, "chinese": 0.0}
    languages: list[str] = []

    for index, result in enumerate(window_results):
        decision = classify_language_code(result.language)
        if result.language:
            languages.append(result.language)
        if decision in scores and result.confidence >= min_confidence:
            scores[decision] += max(result.confidence, 0.01)
        windows.append(
            DetectionWindow(
                path=f"probe-{index}",
                language=result.language,
                confidence=result.confidence,
                decision=decision,
                raw_output=result.raw_output,
            )
        )

    total = scores["english"] + scores["chinese"]
    if total <= 0:
        decision = "uncertain"
        confidence = 0.0
    else:
        english_share = scores["english"] / total
        chinese_share = scores["chinese"] / total
        if english_share >= min_share and english_share - chinese_share >= min_margin:
            decision = "english"
            confidence = english_share
        elif chinese_share >= min_share and chinese_share - english_share >= min_margin:
            decision = "chinese"
            confidence = chinese_share
        else:
            decision = "uncertain"
            confidence = max(english_share, chinese_share)

    detected_language = languages[0] if languages else None
    return LanguageDetectionResult(
        decision=decision,
        confidence=confidence,
        detected_language=detected_language,
        windows=windows,
    )


def detect_primary_language(
    probe_paths: list[Path],
    detector: LanguageDetector,
) -> LanguageDetectionResult:
    results = [detector.detect(path) for path in probe_paths]
    detection = aggregate_language_results(results)
    if detection.decision == "uncertain":
        raise UncertainLanguageError(
            "The main spoken language was not clearly English or Chinese. "
            "Rerun with --profile english or --profile chinese.",
            detection=detection.to_dict(),
        )
    return detection
