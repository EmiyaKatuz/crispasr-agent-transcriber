from __future__ import annotations

from crispasr_agent_transcriber.workflow import _select_model_for_profile


def test_auto_routing_selects_profile_specific_model() -> None:
    options = {
        "model": None,
        "english_model": "models/cohere-transcribe-q4_k.gguf",
        "chinese_model": "models/qwen3-asr-1.7b-q4_k.gguf",
    }

    assert (
        _select_model_for_profile(profile_name="english", **options)
        == "models/cohere-transcribe-q4_k.gguf"
    )
    assert (
        _select_model_for_profile(profile_name="chinese", **options)
        == "models/qwen3-asr-1.7b-q4_k.gguf"
    )


def test_model_override_takes_precedence() -> None:
    assert (
        _select_model_for_profile(
            profile_name="chinese",
            model="models/custom.gguf",
            english_model="models/english.gguf",
            chinese_model="models/chinese.gguf",
        )
        == "models/custom.gguf"
    )
