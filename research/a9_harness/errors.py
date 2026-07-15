"""Stable, fail-closed error types for the A9 research harness."""

from __future__ import annotations


class HarnessError(Exception):
    """An expected harness rejection with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def require(condition: bool, code: str, message: str) -> None:
    """Raise a typed failure when a contract condition is false."""

    if not condition:
        raise HarnessError(code, message)

