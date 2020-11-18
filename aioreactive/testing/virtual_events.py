# type: ignore
import asyncio
import collections
import heapq
import logging
from asyncio import tasks
from asyncio.log import logger

log = logging.getLogger(__name__)

__all__ = "VirtualTimeEventLoop"

# Minimum number of _scheduled timer handles before cleanup of
# cancelled handles is performed.
_MIN_SCHEDULED_TIMER_HANDLES = 100

# Minimum fraction of _scheduled timer handles that are cancelled
# before cleanup of cancelled handles is performed.
_MIN_CANCELLED_TIMER_HANDLES_FRACTION = 0.5


def _format_handle(handle):
    cb = handle._callback
    if isinstance(getattr(cb, "__self__", None), tasks.Task):
        # format the task
        return repr(cb.__self__)
    else:
        return str(handle)


class VirtualTimeEventLoop(asyncio.BaseEventLoop):
    """Virtual time event loop.

    Works the same was as a normal event loop except that time is
    virtual. Time starts at 0 and only advances when something is
    scheduled into the future. Thus the event loops runs as quickly as
    possible while producing the same output as a normal event loop
    would do. This makes it ideal for unit-testing where you want to
    test delays but without spending time in real life.
    """

    def __init__(self) -> None:
        super().__init__()

        self._ready = collections.deque()
        self._current_handle = None
        self._debug = False

        self._time: float = 0.0

    def time(self):
        return self._time

    def _run_once(self):
        """Run one full iteration of the event loop. This calls all
        currently ready callbacks, polls for I/O, schedules the
        resulting callbacks, and finally schedules 'call_later'
        callbacks.
        """
        # log.debug("run_once()")

        sched_count = len(self._scheduled)
        if (
            sched_count > _MIN_SCHEDULED_TIMER_HANDLES
            and self._timer_cancelled_count / sched_count > _MIN_CANCELLED_TIMER_HANDLES_FRACTION
        ):
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

        # print("***", self._ready)
        # print("***", self._scheduled)

        # Handle 'later' callbacks that are ready.
        while self._scheduled and not self._ready:
            handle = self._scheduled[0]
            handle = heapq.heappop(self._scheduled)
            handle._scheduled = False
            log.debug("Advancing time from %s to %s", self._time, handle._when)
            self._time = max(handle._when, self._time)
            self._ready.append(handle)

        # This is the only place where callbacks are actually *called*.
        # All other places just add them to ready. Note: We run all
        # currently scheduled callbacks, but not any callbacks scheduled
        # by callbacks run this time around -- they will be run the next
        # time (after another I/O poll). Use an idiom that is
        # thread-safe without using locks.
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
                        logger.warning("Executing %s took %.3f seconds", _format_handle(handle), dt)
                finally:
                    self._current_handle = None
            else:
                handle._run()
        handle = None  # Needed to break cycles when an exception occurs.

    def _write_to_self(self):
        pass


loop = VirtualTimeEventLoop()
