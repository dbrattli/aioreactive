# import pytest
# import asyncio
# import logging

# from aioreactive.testing import VirtualTimeEventLoop
# from aioreactive.core import AsyncObservable, run, subscribe, AsyncStream, AsyncAnonymousObserver, AsyncIteratorObserver
# from aioreactive.operators.pipe import pipe
# from aioreactive.operators import op, from_async_iterable
# from aioreactive.operators.to_async_iterable import to_async_iterable

# log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)


# @pytest.yield_fixture()
# def event_loop() -> None:
#     loop = VirtualTimeEventLoop()
#     yield loop
#     loop.close()


# @pytest.mark.asyncio
# async def test_async_iteration() -> None:
#     xs = AsyncObservable.from_iterable([1, 2, 3])
#     result = []

#     async for x in to_async_iterable(xs):
#         result.append(x)

#     assert result == [1, 2, 3]


# @pytest.mark.asyncio
# async def test_async_comprehension() -> None:
#     xs = AsyncObservable.from_iterable([1, 2, 3])

#     result = [x async for x in to_async_iterable(xs)]

#     assert result == [1, 2, 3]


# @pytest.mark.asyncio
# async def test_async_iteration_aync_with() -> None:
#     xs = AsyncObservable.from_iterable([1, 2, 3])
#     result = []

#     obv = AsyncIteratorObserver()
#     async with subscribe(xs, obv):
#         async for x in obv:
#             result.append(x)

#     assert result == [1, 2, 3]


# @pytest.mark.asyncio
# async def test_async_iteration_inception() -> None:
#     # iterable to async source to async iterator to async source
#     obv = AsyncIteratorObserver()

#     xs = AsyncObservable.from_iterable([1, 2, 3])
#     await subscribe(xs, obv)
#     ys = from_async_iterable(obv)
#     result = []

#     async for y in to_async_iterable(ys):
#         result.append(y)

#     assert result == [1, 2, 3]


# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(test_async_iteration_inception())
#     loop.close()
