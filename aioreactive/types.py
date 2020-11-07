from abc import abstractmethod
from typing import Callable, Generic, TypeVar

from expression.system import AsyncDisposable

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.
T_contra = TypeVar("T_contra", contravariant=True)  # Ditto contravariant.


class AsyncObserver(Generic[T_contra]):
    """An asynchronous observable."""

    __slots__ = ()

    @abstractmethod
    async def asend(self, value: TSource) -> None:
        raise NotImplementedError

    @abstractmethod
    async def athrow(self, error: Exception) -> None:
        raise NotImplementedError

    @abstractmethod
    async def aclose(self) -> None:
        raise NotImplementedError


class AsyncObservable(Generic[T_co]):
    __slots__ = ()

    @abstractmethod
    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        raise NotImplementedError


Stream = Callable[[AsyncObservable[TSource]], AsyncObservable[TResult]]
"""A stream is a function that transforms from one observable to another."""
