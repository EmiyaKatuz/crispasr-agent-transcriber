from __future__ import annotations

import pytest

from crispasr_agent_transcriber.errors import BackendMismatchError
from crispasr_agent_transcriber.profiles import (
    CHINESE_PROFILE,
    ENGLISH_PROFILE,
    classify_language_code,
    validate_backend_for_profile,
)


def test_language_code_classification() -> None:
    assert classify_language_code("en") == "english"
    assert classify_language_code("zh-CN") == "chinese"
    assert classify_language_code("cmn") == "chinese"
    assert classify_language_code("de") == "unknown"


def test_profiles_use_required_backends() -> None:
    assert ENGLISH_PROFILE.backend == "cohere"
    assert CHINESE_PROFILE.backend == "qwen3-1.7b"


def test_backend_mismatch_includes_one_server_command() -> None:
    with pytest.raises(BackendMismatchError) as exc_info:
        validate_backend_for_profile("cohere", CHINESE_PROFILE, model="C:\\models\\qwen.gguf")
    details = exc_info.value.details
    assert details["expected_backend"] == "qwen3-1.7b"
    assert details["actual_backend"] == "cohere"
    assert details["command"].count("--server") == 1
    assert "qwen3-1.7b" in details["command"]
