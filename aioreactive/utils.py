import logging
from typing import Any, Optional, TypeVar

from .types import AsyncObserver

TSource = TypeVar("TSource")

log = logging.getLogger(__name__)


def noop(*args: Any, **kw: Any) -> None:
    """No operation. Returns nothing"""


async def anoop(value: Optional[Any] = None) -> None:
    """Async no operation. Returns nothing"""


class NoopObserver(AsyncObserver[TSource]):
    async def asend(self, value: TSource) -> None:
        log.debug("NoopSink:asend(%s)", str(value))

    async def athrow(self, error: Exception) -> None:
        log.debug("NoopSink:athrow(%s)", error)

    async def aclose(self) -> None:
        log.debug("NoopSink:aclose()")


noopobserver: NoopObserver[Any] = NoopObserver()
