from typing import Callable, TypeVar
from functools import partial

from aioreactive.core import AsyncSource
from .producer import Producer

T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')


def debounce(seconds: float) -> Callable[[AsyncSource], Producer]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by
    another value before seconds has elapsed.

    Example:
    partial = debounce(5) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value

    Returns a partially applied function that takes a source stream to
    debounce."""

    from aioreactive.core.sources.debounce import debounce
    return partial(debounce, seconds)


def delay(seconds: float) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.delay import delay
    return partial(delay, seconds)


def filter(predicate: Callable[[T], bool]) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.filter import filter
    return partial(filter, predicate)


def flat_map(fn: Callable[[T], AsyncSource]) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.flat_map import flat_map
    return partial(flat_map, fn)


def map(fn: Callable) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.map import map
    return partial(map, fn)


def merge(other: AsyncSource) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.merge import merge
    return partial(merge, other)


def with_latest_from(mapper: Callable, other: AsyncSource) -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.with_latest_from import with_latest_from
    return partial(with_latest_from, mapper, other)


def distinct_until_changed() -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.distinct_until_changed import distinct_until_changed
    return partial(distinct_until_changed)


def switch_latest() -> Callable[[AsyncSource], Producer]:
    from aioreactive.core.sources.switch_latest import switch_latest
    return partial(switch_latest)
