"""Example to show how to split a stream into two substreams."""
import asyncio

from aioreactive.core import start, FuncSink

from aioreactive.producer import Producer
import aioreactive.producer.operators as ops


async def main():
    xs = Producer.from_iterable(range(10))

    # Split into odds and evens
    odds = xs | ops.filter(lambda x: x % 2 == 1)
    evens = xs | ops.filter(lambda x: x % 2 == 0)

    async def mysink(value):
        print(value)

    await start(odds, FuncSink(mysink))
    await start(evens, FuncSink(mysink))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
