from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .crispasr_manager import BIN_DIR as DEFAULT_BIN_DIR
from .crispasr_manager import ensure_binary, find_binary
from .errors import ServerError
from .profiles import TranscriptionProfile


@dataclass
class ManagedCrispASRServer:
    profile: TranscriptionProfile
    crispasr_bin: str = "crispasr"
    model: str | None = None
    host: str = "127.0.0.1"
    port: int = 8080
    keep_server: bool = False
    startup_timeout_seconds: float = 120.0
    extra_args: list[str] = field(default_factory=list)
    process: subprocess.Popen | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @classmethod
    def with_auto_install(
        cls,
        profile: TranscriptionProfile,
        *,
        model: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        keep_server: bool = False,
        bin_dir: str | None = None,
        **kwargs,
    ) -> ManagedCrispASRServer:
        bin_path = find_binary(bin_dir=Path(bin_dir) if bin_dir else DEFAULT_BIN_DIR)
        if bin_path is None:
            bin_path = ensure_binary(
                bin_dir=Path(bin_dir) if bin_dir else DEFAULT_BIN_DIR,
                auto_install=True,
            )
        return cls(
            profile=profile,
            crispasr_bin=str(bin_path) if bin_path else "crispasr",
            model=model,
            host=host,
            port=port,
            keep_server=keep_server,
            **kwargs,
        )

    def build_command(self) -> list[str]:
        return [
            *self.profile.server_command(
                crispasr_bin=self.crispasr_bin,
                model=self.model,
                host=self.host,
                port=self.port,
            ),
            *self.extra_args,
        ]

    def start(self) -> str:
        if self.process is not None:
            return self.base_url
        command = self.build_command()
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise ServerError(
                "CrispASR binary was not found; install CrispASR or pass --crispasr-bin.",
                command=command,
            ) from exc
        self._wait_for_health()
        return self.base_url

    def _wait_for_health(self) -> None:
        deadline = time.monotonic() + self.startup_timeout_seconds
        last_error = ""
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=1)
                raise ServerError(
                    "CrispASR server exited before it became ready.",
                    command=self.build_command(),
                    stdout=stdout[-2000:],
                    stderr=stderr[-2000:],
                )
            try:
                response = httpx.get(f"{self.base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    return
                last_error = response.text[:500]
            except httpx.HTTPError as exc:
                last_error = str(exc)
            time.sleep(0.5)
        raise ServerError(
            "Timed out waiting for CrispASR server to become ready.",
            command=self.build_command(),
            last_error=last_error,
        )

    def stop(self) -> None:
        if self.keep_server or self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.process = None

    def __enter__(self) -> ManagedCrispASRServer:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()
