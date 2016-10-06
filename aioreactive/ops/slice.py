from aioreactive.abc import AsyncSource

from .filteri import filteri

from .skip import skip
from .take import take
from .take_last import take_last
from .skip_last import skip_last


def slice(start=None, stop=None, step=1, source=None) -> AsyncSource:
    """Slices the given source stream.

    It is basically a wrapper around skip(), skip_last(), take(),
    take_last() and filter().

    This marble diagram helps you remember how slices works with
    streams. Positive numbers is relative to the start of the events,
    while negative numbers are relative to the end (on_completed) of the
    stream.

    r---e---a---c---t---i---v---e---|
    0   1   2   3   4   5   6   7   8
   -8  -7  -6  -5  -4  -3  -2  -1

    Example:
    result = slice(1, 10, source)
    result = slice(1, -2, source)
    result = slice(1, -1, 2, source)

    Keyword arguments:
    start -- Number of elements to skip of take last
    stop -- Last element to take of skip last
    step -- Takes every step element. Must be larger than zero
    source -- Source stream to slice

    Returns a sliced source stream.
    """

    if start is not None:
        if start < 0:
            source = take_last(abs(start), source)
        else:
            source = skip(start, source)

    if stop is not None:
        if stop > 0:
            start = start or 0
            source = take(stop - start, source)
        else:
            source = skip_last(abs(stop), source)

    if step is not None:
        if step > 1:
            source = filteri(lambda x, i: i % step == 0, source)
        elif step < 0:
            # Reversing streams is not supported
            raise TypeError("Negative step not supported.")

    return source
