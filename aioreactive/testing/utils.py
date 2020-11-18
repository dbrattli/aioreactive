from pytest import approx


def ca(value: float):
    """Approx with millisecond accuracy."""

    return approx(value, rel=0.001)


__all__ = ["ca"]
