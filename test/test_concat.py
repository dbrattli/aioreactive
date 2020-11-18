import logging

import aioreactive as rx
import pytest
from expression.core import pipe

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_concat_happy():
    xs = rx.from_iterable(range(5))
    ys = rx.from_iterable(range(5, 10))
    result = []

    async def asend(value: int) -> None:
        result.append(value)

    zs = pipe(xs, rx.concat(ys))

    obv: rx.AsyncObserver[int] = rx.AsyncAwaitableObserver(asend)
    await rx.run(zs, obv)
    assert result == list(range(10))
