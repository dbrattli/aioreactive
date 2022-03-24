from abc import abstractmethod
from typing import (
    Awaitable,
    Callable,
    Generic,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
)

from expression.system import AsyncDisposable

_T = TypeVar("_T")
TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
_T_out = TypeVar("_T_out", covariant=True)  # Any type covariant containers.
_T_in = TypeVar("_T_in", contravariant=True)  # Ditto contravariant.

SendAsync = Callable[[_T], Awaitable[None]]
ThrowAsync = Callable[[Exception], Awaitable[None]]
CloseAsync = Callable[[], Awaitable[None]]


class AsyncObserver(Generic[_T_in]):
    """An asynchronous observable."""

    __slots__ = ()

    @abstractmethod
    async def asend(self, value: _T_in) -> None:
        raise NotImplementedError

    @abstractmethod
    async def athrow(self, error: Exception) -> None:
        raise NotImplementedError

    @abstractmethod
    async def aclose(self) -> None:
        raise NotImplementedError


class AsyncObservable(Generic[_T_out]):
    __slots__ = ()

    @abstractmethod
    async def subscribe_async(
        self,
        send: Optional[Union[SendAsync[_T_out], AsyncObserver[_T_out]]] = None,
        throw: Optional[ThrowAsync] = None,
        close: Optional[CloseAsync] = None,
    ) -> AsyncDisposable:
        raise NotImplementedError


class Projection2(Protocol[_T_in, _T_out]):
    """A projetion is a function that transforms from one observable to another, i.e:

    `AsyncObservable[TSource]) -> AsyncObservable[TResult]`
    """

    def __call__(self, __source: AsyncObservable[_T_in]) -> AsyncObservable[_T_out]:
        raise NotImplementedError


class Zipper(Protocol[TSource, _T_out]):
    """A zipping projetion is a function that projects from one observable to a zipped, i.e:

    `AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TResult]]`
    """

    def __call__(
        self, __source: AsyncObservable[TSource]
    ) -> AsyncObservable[Tuple[TSource, _T_out]]:
        raise NotImplementedError


class Flatten(Protocol):
    """A zipping projetion is a function that projects from one observable to a zipped, i.e:

    `AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[Tuple[TSource, TResult]]`
    """

    def __call__(
        self, __source: AsyncObservable[AsyncObservable[TSource]]
    ) -> AsyncObservable[TSource]:
        raise NotImplementedError


__all__ = ["AsyncObserver", "AsyncObservable"]
