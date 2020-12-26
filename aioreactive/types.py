from abc import abstractmethod
from typing import Generic, Protocol, Tuple, TypeVar

from expression.system import AsyncDisposable

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.
T_contra = TypeVar("T_contra", contravariant=True)  # Ditto contravariant.


class AsyncObserver(Generic[T_contra]):
    """An asynchronous observable."""

    __slots__ = ()

    @abstractmethod
    async def asend(self, value: T_contra) -> None:
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
    async def subscribe_async(self, observer: AsyncObserver[T_co]) -> AsyncDisposable:
        raise NotImplementedError


class Projection(Protocol[TSource, TResult]):
    """A projetion is a function that transforms from one observable to another, i.e:

    `AsyncObservable[TSource]) -> AsyncObservable[TResult]`
    """

    def __call__(self, __source: AsyncObservable[TSource]) -> AsyncObservable[TResult]:
        raise NotImplementedError


class Zipper(Protocol[TResult]):
    """A zipping projetion is a function that projects from one observable to a zipped, i.e:

    `AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TResult]]`
    """

    def __call__(self, __source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TResult]]:
        raise NotImplementedError


class Filter(Protocol):
    """A filter projetion is a function that projects from one observable to the same, i.e:

    `AsyncObservable[TSource]) -> AsyncObservable[TSource]`
    """

    def __call__(self, __source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        raise NotImplementedError
