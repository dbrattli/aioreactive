from typing import Callable, Iterable, Tuple, TypeVar

from fslash.system import AsyncDisposable

from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, auto_detach_observer
from .types import AsyncObservable, AsyncObserver

TSource = TypeVar("TSource")
TOther = TypeVar("TOther")


def zip_seq(
    sequence: Iterable[TOther],
) -> Callable[[AsyncObservable[TSource]], AsyncObservable[Tuple[TSource, TOther]]]:
    def _(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
        async def subscribe_async(aobv: AsyncObserver[Tuple[TSource, TOther]]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            enumerator = iter(sequence)

            async def asend(x: TSource) -> None:
                try:
                    try:
                        n = next(enumerator)
                        await safe_obv.asend((x, n))
                    except StopIteration:
                        await safe_obv.aclose()
                except Exception as ex:
                    await safe_obv.athrow(ex)

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            async def aclose() -> None:
                await safe_obv.aclose()

            _obv = AsyncAnonymousObserver(asend, athrow, aclose)
            return await auto_detach(source.subscribe_async(_obv))

        return AsyncAnonymousObservable(subscribe_async)

    return _
