import asyncio
from typing import TypeVar
from collections.abc import Awaitable
import logging

from .typing import AsyncSource, AsyncSink
from .futures import Subscription, chain_future

log = logging.getLogger(__name__)

T = TypeVar("T")


class SubscriptionFactory(Awaitable):
    """A helper class that makes it possible to setup subscriptions both
    using await and async-with."""

    def __init__(self, source, sink=None):
        self._source = source
        self._sink = sink

        self._subscription = None

    async def create(self) -> Subscription:
        """Awaits subscription.

        Awaits until subscription has been setup, and returns
        a subscription future. The future will resolve to the
        last value received in the stream of values."""

        if self._sink is not None:
            down = await Subscription().__alisten__(self._sink)
        else:
            down = Subscription()

        up = await self._source.__alisten__(down)
        self._subscription = chain_future(down, up)

        return self._subscription

    async def __aenter__(self) -> Subscription:
        """Awaits subscription."""
        return await self.create()

    async def __aexit__(self, type, value, traceback) -> None:
        """Closes subscription."""
        self._subscription.cancel()

    def __await__(self) -> Subscription:
        """Await subscription."""
        return self.create().__await__()


def listen(source: AsyncSource, sink: AsyncSink=None) -> SubscriptionFactory:
    return SubscriptionFactory(source, sink)


async def run(source: AsyncSource, asink: AsyncSink, timeout: int=2) -> T:
    """Awaits until subscription closes and returns the final value"""
    return await asyncio.wait_for(await listen(source, asink), timeout)
