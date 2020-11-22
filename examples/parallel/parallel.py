import asyncio
import logging
import time
from asyncio.futures import wrap_future
from concurrent.futures import ThreadPoolExecutor
from threading import current_thread

import aioreactive as rx
from expression.core import pipe

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

executor = ThreadPoolExecutor(max_workers=10)


def long_running(value: int) -> int:
    print("Long running ({0}) on thread {1}".format(value, current_thread().name))
    time.sleep(3)
    print("Long running, done ({0}) on thread {1}".format(value, current_thread().name))
    return value


async def main() -> None:
    xs = rx.from_iterable([1, 2, 3, 4, 5])

    async def mapper(value: int) -> rx.AsyncObservable[int]:
        fut = executor.submit(long_running, value)
        return rx.of_async(wrap_future(fut))

    ys = pipe(
        xs,
        rx.flat_map_async(mapper),
        rx.to_async_iterable,
    )
    async for x in ys:
        print(x)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
