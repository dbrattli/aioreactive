from typing import AsyncIterable
import itertools
import builtins


async def repeat(value, times=None) -> AsyncIterable:
    for value in itertools.repeat(value, times):
        yield value


async def range(*args) -> AsyncIterable:
    for value in builtins.range(*args):
        yield value


async def filter(predicate, source: AsyncIterable) -> AsyncIterable:
    async for value in source:
        if predicate(value):
            yield value


async def map(func, source: AsyncIterable) -> AsyncIterable:
    async for value in source:
        yield func(value)

