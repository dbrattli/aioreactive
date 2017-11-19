from typing import Callable, TypeVar, AsyncIterable
from functools import partial

from .typing import AsyncObservable

T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')


class Operators:
    """A collection of partially appliable and lazy loaded operators."""

    @staticmethod
    def debounce(seconds: float) -> Callable[[AsyncObservable[T]], AsyncObservable[T]]:
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

    @staticmethod
    def delay(seconds: float) -> Callable[[AsyncObservable[T]], AsyncObservable[T]]:
        from aioreactive.operators.delay import delay
        return partial(delay, seconds)

    @staticmethod
    def filter(predicate: Callable[[T], bool]) -> Callable[[AsyncObservable[T]], AsyncObservable[T]]:
        from aioreactive.operators.filter import filter
        return partial(filter, predicate)

    @staticmethod
    def flat_map(fn: Callable[[T], AsyncObservable]) -> Callable[[AsyncObservable], AsyncObservable]:
        from aioreactive.operators.flat_map import flat_map
        return partial(flat_map, fn)

    @staticmethod
    def map(fn: Callable) -> Callable[[AsyncObservable[T1]], AsyncObservable[T2]]:
        from aioreactive.operators.map import map as _map
        return partial(_map, fn)

    @staticmethod
    def merge(other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
        from aioreactive.operators.merge import merge
        return partial(merge, other)

    @staticmethod
    def with_latest_from(mapper: Callable, other: AsyncObservable) -> Callable[[AsyncObservable], AsyncObservable]:
        from aioreactive.operators.with_latest_from import with_latest_from
        return partial(with_latest_from, mapper, other)

    @staticmethod
    def distinct_until_changed() -> Callable[[AsyncObservable], AsyncObservable]:
        from aioreactive.operators.distinct_until_changed import distinct_until_changed
        return partial(distinct_until_changed)

    @staticmethod
    def switch_latest() -> Callable[[AsyncObservable], AsyncObservable]:
        from aioreactive.operators.switch_latest import switch_latest
        return partial(switch_latest)

    @staticmethod
    def to_async_iterable() -> Callable[[AsyncObservable], AsyncIterable]:
        from aioreactive.operators.to_async_iterable import to_async_iterable
        return partial(to_async_iterable)
