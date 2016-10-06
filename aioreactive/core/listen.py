import asyncio
import logging
from typing import TypeVar

from aioreactive.abc import AsyncSource, AsyncSink

from .utils import anoop
from .futures import Subscription, chain_future

T = TypeVar('T')
log = logging.getLogger(__name__)


class Listener(AsyncSink):
    """An anonymous async sink.

    Used for listening to a source"""

    def __init__(self, send=anoop, throw=anoop, close=anoop):
        self._send = send
        self._throw = throw
        self._close = close

    async def send(self, value):
        await self._send(value)

    async def throw(self, ex):
        await self._throw(ex)

    async def close(self):
        await self._close()


async def listen(source: AsyncSource, sink: AsyncSink=None) -> Subscription:
    """Awaits subscription.

    Awaits until subscriptions has been setup, and returns
    a subscription future. The future will resolve to the
    last value received in the stream of values."""

    if sink is not None:
        down = await Subscription().__alisten__(sink)
    else:
        down = Subscription()

    up = await source.__alisten__(down)
    return chain_future(down, up)


async def run(source: AsyncSource, asink: AsyncSink, timeout: int=2) -> T:
    """Awaits until subscription closes and returns the final value"""
    return await asyncio.wait_for(await listen(source, asink), timeout)
