from pytest import approx


def ca(value: float):
    """Approx with millisecond accuracy."""

    return approx(value, rel=0.005)


__all__ = ["ca"]
