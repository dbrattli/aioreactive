from typing import Union, Awaitable, Callable, TypeVar

from aioreactive.core.typing import AsyncSource

from .switch_latest import switch_latest
from .merge import merge
from .map import map

T1 = TypeVar('T1')
T2 = TypeVar('T2')


def flat_map(fn: Union[Callable[[T1], AsyncSource[T2]], Awaitable[T1]], source: AsyncSource[T2]) -> AsyncSource[T2]:
    """Project each element of a source stream into a new source stream
    and merges the resulting source streams back into a single source
    stream.

    xs = flat_map(lambda x: range(0, x), source)

    Keyword arguments:
    fn -- A transform function to apply to each element of the source
        stream.

    Returns a source stream whose elements are the result of
    invoking the one-to-many transform function on each element of the
    input source and then mapping each of those source elements and
    their corresponding source element to a result element."""

    return merge(map(fn, source))


def flat_map_latest(fn: Union[Callable[[T1], AsyncSource[T2]], Awaitable[T1]], source: AsyncSource[T2]) -> AsyncSource[T2]:
    return switch_latest(map(fn, source))
