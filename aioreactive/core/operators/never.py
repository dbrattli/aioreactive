from aioreactive.core import AsyncObserver, AsyncObservable, AsyncSingleStream


class Never(AsyncObservable):
    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncSingleStream:
        return AsyncSingleStream()


def never() -> AsyncObservable:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source steam where nothing happens.
    """

    return Never()
