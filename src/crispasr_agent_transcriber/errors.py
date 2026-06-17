from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranscriberError(Exception):
    """Base error with a stable code for CLI and MCP callers."""

    message: str
    code: str = "transcriber_error"
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            data["details"] = self.details
        return data


class PathValidationError(TranscriberError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message=message, code="invalid_local_path", details=details)


class MediaError(TranscriberError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message=message, code="media_error", details=details)


class LanguageDetectionError(TranscriberError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message=message, code="language_detection_failed", details=details)


class UncertainLanguageError(LanguageDetectionError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message, **details)
        self.code = "language_uncertain"


class ServerError(TranscriberError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message=message, code="crispasr_server_error", details=details)


class BackendMismatchError(ServerError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message, **details)
        self.code = "backend_mismatch"


class CrispASRRequestError(TranscriberError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message=message, code="crispasr_request_failed", details=details)
