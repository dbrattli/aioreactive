from typing import Callable

from aioreactive.core import AsyncObservable


def pipe(source: AsyncObservable, *args: Callable[[AsyncObservable], AsyncObservable]) -> AsyncObservable:
    for op in args:
        source = op(source)
    return source
