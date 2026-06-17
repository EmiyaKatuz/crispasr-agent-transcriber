from __future__ import annotations

from crispasr_agent_transcriber.profiles import CHINESE_PROFILE
from crispasr_agent_transcriber.server_manager import ManagedCrispASRServer


class FakeProcess:
    def poll(self):
        return None

    def terminate(self) -> None:
        pass

    def wait(self, timeout=None):
        return 0


def test_managed_server_builds_one_backend_command(monkeypatch) -> None:
    calls = []

    def fake_popen(command, **_kwargs):
        calls.append(command)
        return FakeProcess()

    monkeypatch.setattr("subprocess.Popen", fake_popen)
    monkeypatch.setattr(ManagedCrispASRServer, "_wait_for_health", lambda self: None)

    server = ManagedCrispASRServer(
        profile=CHINESE_PROFILE,
        model="models/qwen3-asr-1.7b-q4_k.gguf",
    )
    assert server.start() == "http://127.0.0.1:8080"
    assert len(calls) == 1
    assert calls[0].count("--server") == 1
    assert "qwen3-1.7b" in calls[0]
    server.stop()
