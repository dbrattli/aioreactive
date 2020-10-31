import asyncio
import heapq
import inspect
import logging
import threading
from asyncio import TimerHandle

log = logging.getLogger(__name__)


def _format_handle(handle):
    cb = handle._callback
    if inspect.ismethod(cb) and isinstance(cb.__self__, asyncio.Task):
        # format the task
        return repr(cb.__self__)
    else:
        return str(handle)


def _run_until_complete_cb(fut):
    exc = fut._exception
    if isinstance(exc, BaseException) and not isinstance(exc, Exception):
        # Issue #22429: run_forever() already finished, no need to
        # stop it.
        return
    fut._loop.stop()


class VirtualTimeEventLoop(asyncio.BaseEventLoop):
    def __init__(self) -> None:
        super().__init__()

        self._exception_handler = None
        self._current_handle = None
        self._debug = False
        self._time = 0

    def time(self):
        return self._time

    def _run_once(self):
        print("_run_once(), time=", self._time)
        # Handle 'later' callbacks that are ready.

        sched_count = len(self._scheduled)
        if sched_count and self._timer_cancelled_count:
            # Remove delayed calls that were cancelled if their number
            # is too high
            new_scheduled = []
            for handle in self._scheduled:
                if handle._cancelled:
                    handle._scheduled = False
                else:
                    new_scheduled.append(handle)

            heapq.heapify(new_scheduled)
            self._scheduled = new_scheduled
            self._timer_cancelled_count = 0
        else:
            # Remove delayed calls that were cancelled from head of queue.
            while self._scheduled and self._scheduled[0]._cancelled:
                self._timer_cancelled_count -= 1
                handle = heapq.heappop(self._scheduled)
                handle._scheduled = False

        # Process callbacks one at a time and advance time
        if self._scheduled and not self._ready:
            handle = self._scheduled[0]
            handle = heapq.heappop(self._scheduled)
            handle._scheduled = False
            self._time = handle._when
            self._ready.append(handle)

        ntodo = len(self._ready)
        for i in range(ntodo):
            handle = self._ready.popleft()
            if handle._cancelled:
                continue
            if self._debug:
                try:
                    self._current_handle = handle
                    t0 = self.time()
                    handle._run()
                    dt = self.time() - t0
                    if dt >= self.slow_callback_duration:
                        log.warning("Executing %s took %.3f seconds", _format_handle(handle), dt)
                finally:
                    self._current_handle = None
            else:
                handle._run()
        handle = None  # Needed to break cycles when an exception occurs.


loop = VirtualTimeEventLoop()
