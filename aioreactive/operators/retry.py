from itertools import repeat
from typing import TypeVar

from aioreactive.core import AsyncObservable

from .catch_exception import catch_exception

T = TypeVar('T')


def retry(source: AsyncObservable[T], retry_count: int=None) -> AsyncObservable[T]:
    """Repeat source observable.

    Repeats the source observable sequence the specified number of times
    or until it successfully terminates. If the retry count is not
    specified, it retries indefinitely.

    1 - retried = retry.repeat()
    2 - retried = retry.repeat(42)

    retry_count -- [Optional] Number of times to retry the sequence. If not
    provided, retry the sequence indefinitely.

    Returns an observable sequence producing the elements of the given
    sequence repeatedly until it terminates successfully.
    """
    return catch_exception(repeat(source, retry_count))
