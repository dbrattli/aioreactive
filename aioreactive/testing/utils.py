from typing import Any


def ca(value: float) -> Any:
    """Approx with millisecond accuracy."""
    from pytest import approx  # type: ignore

    return approx(value, rel=0.005)  # type: ignore


__all__ = ["ca"]
