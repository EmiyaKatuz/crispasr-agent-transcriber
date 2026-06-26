from __future__ import annotations

from pathlib import Path

import pytest

from crispasr_agent_transcriber.errors import TranscriberError
from crispasr_agent_transcriber.models import (
    download_model,
    get_model_spec,
    list_model_options,
    recommended_model_ids,
    resolve_recommended_model_paths,
)


class _FakeResponse:
    def __init__(self) -> None:
        self._pending = b"model-bytes"

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def read(self, _size=-1):
        chunk = self._pending
        self._pending = b""
        return chunk


def test_recommended_models_are_balanced_bundle(tmp_path: Path) -> None:
    assert recommended_model_ids() == ["english-q4", "chinese-q4", "lid-q4"]

    options = list_model_options(tmp_path)
    assert options["ready"] is False
    assert set(options["recommended_paths"]) == {"english", "chinese", "lid"}
    assert options["recommended_paths"]["english"].endswith("cohere-transcribe-q4_k.gguf")
    assert options["recommended_paths"]["lid"].endswith("firered-lid-q4_k.gguf")


def test_get_model_spec_accepts_id_or_filename() -> None:
    by_id = get_model_spec("english-q4")
    by_file = get_model_spec("cohere-transcribe-q4_k.gguf")
    assert by_id == by_file


def test_model_dir_rejects_urls() -> None:
    with pytest.raises(TranscriberError) as exc:
        list_model_options("https://example.com/models")
    assert exc.value.code == "invalid_model_dir"


def test_download_model_writes_partial_then_manifest(tmp_path: Path, monkeypatch) -> None:
    def fake_urlopen(*_args, **_kwargs):
        return _FakeResponse()

    monkeypatch.setattr("crispasr_agent_transcriber.models.urllib.request.urlopen", fake_urlopen)
    result = download_model("english-q4", models_dir=tmp_path)

    model_path = tmp_path / "cohere-transcribe-q4_k.gguf"
    assert result["downloaded"] is True
    assert model_path.read_bytes() == b"model-bytes"
    assert (tmp_path / "model-manifest.json").is_file()
    assert not (tmp_path / "cohere-transcribe-q4_k.gguf.part").exists()


def test_resolve_paths_reports_ready_when_recommended_exist(tmp_path: Path) -> None:
    for filename in [
        "cohere-transcribe-q4_k.gguf",
        "qwen3-asr-1.7b-q4_k.gguf",
        "firered-lid-q4_k.gguf",
    ]:
        (tmp_path / filename).write_bytes(b"model")

    paths = resolve_recommended_model_paths(tmp_path)
    assert paths["ready"] is True
    assert paths["english_model"].endswith("cohere-transcribe-q4_k.gguf")
    assert paths["chinese_model"].endswith("qwen3-asr-1.7b-q4_k.gguf")
    assert paths["lid_model"].endswith("firered-lid-q4_k.gguf")
