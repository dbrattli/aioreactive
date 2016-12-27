from typing import Callable, TypeVar
from functools import partial

from aioreactive.core import AsyncObservable

T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')


def debounce(seconds: float) -> Callable[[AsyncObservable], AsyncObservable]:
    """Debounce source stream.

    Ignores values from a source stream which are followed by
    another value before seconds has elapsed.

    Example:
    partial = debounce(5) # 5 seconds

    Keyword arguments:
    seconds -- Duration of the throttle period for each value

    Returns a partially applied function that takes a source stream to
    debounce."""

    from aioreactive.operators.debounce import debounce
    return partial(debounce, seconds)


def delay(seconds: float) -> Callable[[AsyncObservable], AsyncObservable]:
    from .delay import delay
    return partial(delay, seconds)


def filter(predicate: Callable[[T], bool]) -> Callable[[AsyncObservable], AsyncObservable]:
    from .filter import filter
    return partial(filter, predicate)


def flat_map(fn: Callable[[T], AsyncObservable]) -> Callable[[AsyncObservable], AsyncObservable]:
    from .flat_map import flat_map
    return partial(flat_map, fn)


def map(fn: Callable) -> Callable[[AsyncObservable], AsyncObservable]:
    from .map import map as _map
    return partial(_map, fn)


def merge(other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from .merge import merge
    return partial(merge, other)


def with_latest_from(mapper: Callable, other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
    from .with_latest_from import with_latest_from
    return partial(with_latest_from, mapper, other)


def distinct_until_changed() -> Callable[[AsyncObservable], AsyncObservable]:
    from .distinct_until_changed import distinct_until_changed
    return partial(distinct_until_changed)


def switch_latest() -> Callable[[AsyncObservable], AsyncObservable]:
    from .switch_latest import switch_latest
    return partial(switch_latest)


def pipe(source: AsyncObservable, *args: Callable[[AsyncObservable], AsyncObservable]) -> AsyncObservable:
    for op in args:
        source = op(source)
    return source
