from __future__ import annotations

import pytest

from crispasr_agent_transcriber.errors import UncertainLanguageError
from crispasr_agent_transcriber.language import (
    WindowLanguage,
    aggregate_language_results,
    detect_primary_language,
    parse_language_output,
)


class FakeDetector:
    def __init__(self, results: list[WindowLanguage]) -> None:
        self.results = results

    def detect(self, _audio_path):
        return self.results.pop(0)


def test_parse_json_language_output() -> None:
    parsed = parse_language_output('{"language": "zh", "confidence": 0.91}')
    assert parsed.language == "zh"
    assert parsed.confidence == 0.91


def test_aggregate_routes_english() -> None:
    result = aggregate_language_results(
        [
            WindowLanguage("en", 0.9, ""),
            WindowLanguage("en-US", 0.8, ""),
            WindowLanguage("en", 0.7, ""),
        ]
    )
    assert result.decision == "english"


def test_aggregate_routes_chinese() -> None:
    result = aggregate_language_results(
        [
            WindowLanguage("zh", 0.9, ""),
            WindowLanguage("cmn", 0.8, ""),
            WindowLanguage("zh-CN", 0.7, ""),
        ]
    )
    assert result.decision == "chinese"


def test_mixed_language_is_uncertain() -> None:
    result = aggregate_language_results(
        [
            WindowLanguage("zh", 0.9, ""),
            WindowLanguage("en", 0.88, ""),
        ]
    )
    assert result.decision == "uncertain"


def test_detect_primary_language_raises_on_uncertain(tmp_path) -> None:
    probe = tmp_path / "probe.wav"
    probe.write_bytes(b"not real audio")
    detector = FakeDetector([WindowLanguage("de", 0.9, "")])
    with pytest.raises(UncertainLanguageError):
        detect_primary_language([probe], detector)
