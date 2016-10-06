import inspect
import traceback
import logging
import threading
import collections
import heapq
import asyncio
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
    if (isinstance(exc, BaseException) and not isinstance(exc, Exception)):
        # Issue #22429: run_forever() already finished, no need to
        # stop it.
        return
    fut._loop.stop()


def isfuture(obj):
    """Check for a Future.
    This returns True when obj is a Future instance or is advertising
    itself as duck-type compatible by setting _asyncio_future_blocking.
    See comment in Future for more details.
    """
    return getattr(obj, '_asyncio_future_blocking', None) is not None


class VirtualTimeEventLoop(asyncio.AbstractEventLoop):
    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        self._ready = collections.deque()
        self._scheduled = []
        self._thread_id = None
        self._exception_handler = None
        self._current_handle = None
        self._debug = False
        self._time = 0

    def run_forever(self):
        """Run until stop() is called."""
        self._check_closed()

        if self.is_running():
            raise RuntimeError('Event loop is running.')

        self._thread_id = threading.get_ident()
        try:
            while True:
                self._run_once()
                if self._stopping:
                    break
        finally:
            self._stopping = False
            self._thread_id = None

    def run_until_complete(self, future):
        """Run the event loop until a Future is done.
        Return the Future's result, or raise its exception.
        """
        self._check_closed()

        new_task = not isfuture(future)
        future = asyncio.ensure_future(future, loop=self)
        if new_task:
            # An exception is raised if the future didn't complete, so there
            # is no need to log the "destroy pending task" message
            future._log_destroy_pending = False

        future.add_done_callback(_run_until_complete_cb)
        try:
            self.run_forever()
        except:
            if new_task and future.done() and not future.cancelled():
                # The coroutine raised a BaseException. Consume the exception
                # to not log a warning, the caller doesn't have access to the
                # local task.
                future.exception()
            raise
        future.remove_done_callback(_run_until_complete_cb)
        if not future.done():
            raise RuntimeError('Event loop stopped before Future completed.')

        return future.result()

    def stop(self):
        """Stop running the event loop.
        Every callback already scheduled will still run.  This simply informs
        run_forever to stop looping after a complete iteration.
        """
        self._stopping = True

    def close(self):
        """Close the event loop.
        This clears the queues and shuts down the executor,
        but does not wait for the executor to finish.
        The event loop must not be running.
        """
        if self.is_running():
            raise RuntimeError("Cannot close a running event loop")
        if self._closed:
            return

        self._closed = True
        self._ready.clear()
        self._scheduled.clear()

    def is_closed(self):
        """Returns True if the event loop was closed."""
        return self._closed

    def is_running(self):
        """Returns True if the event loop is running."""
        return (self._thread_id is not None)

    def call_later(self, delay, callback, *args):
        timer = self.call_at(self.time() + delay, callback, *args)
        if timer._source_traceback:
            del timer._source_traceback[-1]
        return timer

    def call_at(self, when, callback, *args):
        timer = TimerHandle(when, callback, args, self)
        if timer._source_traceback:
            del timer._source_traceback[-1]
        heapq.heappush(self._scheduled, timer)
        timer._scheduled = True
        return timer

    def call_soon(self, callback, *args):
        handle = self._call_soon(callback, args)
        if handle._source_traceback:
            del handle._source_traceback[-1]
        return handle

    def _call_soon(self, callback, args):
        if (asyncio.iscoroutine(callback) or asyncio.iscoroutinefunction(callback)):
            raise TypeError("coroutines cannot be used with call_soon()")
        self._check_closed()
        handle = asyncio.Handle(callback, args, self)
        if handle._source_traceback:
            del handle._source_traceback[-1]
        self._ready.append(handle)
        return handle

    def call_soon_threadsafe(self, callback, *args):
        raise NotImplementedError

    def time(self):
        return self._time

    def create_future(self):
        """Create a Future object attached to the loop."""
        return asyncio.Future(loop=self)

    def create_task(self, coro):
        """Schedule a coroutine object.
        Return a task object."""

        self._check_closed()
        task = asyncio.Task(coro, loop=self)
        if task._source_traceback:
            del task._source_traceback[-1]
        return task

    def default_exception_handler(self, context):
        """Default exception handler.
        This is called when an exception occurs and no exception
        handler is set, and can be called by a custom exception
        handler that wants to defer to the default behavior.
        The context parameter has the same meaning as in
        `call_exception_handler()`."""

        message = context.get('message')
        if not message:
            message = 'Unhandled exception in event loop'

        exception = context.get('exception')
        if exception is not None:
            exc_info = (type(exception), exception, exception.__traceback__)
        else:
            exc_info = False

        if ('source_traceback' not in context
        and self._current_handle is not None
        and self._current_handle._source_traceback):
            context['handle_traceback'] = self._current_handle._source_traceback

        log_lines = [message]
        for key in sorted(context):
            if key in {'message', 'exception'}:
                continue
            value = context[key]
            if key == 'source_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Object created at (most recent call last):\n'
                value += tb.rstrip()
            elif key == 'handle_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Handle created at (most recent call last):\n'
                value += tb.rstrip()
            else:
                value = repr(value)
            log_lines.append('{}: {}'.format(key, value))

        log.error('\n'.join(log_lines), exc_info=exc_info)

    def call_exception_handler(self, context):
        """Call the current event loop's exception handler.
        The context argument is a dict containing the following keys:
        - 'message': Error message;
        - 'exception' (optional): Exception object;
        - 'future' (optional): Future instance;
        - 'handle' (optional): Handle instance;
        - 'protocol' (optional): Protocol instance;
        - 'transport' (optional): Transport instance;
        - 'socket' (optional): Socket instance;
        - 'asyncgen' (optional): Asynchronous generator that caused
                                 the exception.
        New keys maybe introduced in the future.
        Note: do not overload this method in an event loop subclass.
        For custom exception handling, use the
        `set_exception_handler()` method.
        """
        if self._exception_handler is None:
            try:
                self.default_exception_handler(context)
            except Exception:
                # Second protection layer for unexpected errors
                # in the default implementation, as well as for subclassed
                # event loops with overloaded "default_exception_handler".
                log.error('Exception in default exception handler', exc_info=True)
        else:
            try:
                self._exception_handler(self, context)
            except Exception as exc:
                # Exception in the user set custom exception handler.
                try:
                    # Let's try default handler.
                    self.default_exception_handler({
                        'message': 'Unhandled error in exception handler',
                        'exception': exc,
                        'context': context,
                    })
                except Exception:
                    # Guard 'default_exception_handler' in case it is
                    # overloaded.
                    log.error('Exception in default exception handler '
                              'while handling an unexpected error '
                              'in custom exception handler',
                              exc_info=True)

    def get_debug(self):
        return self._debug

    def _run_once(self):
        # Handle 'later' callbacks that are ready.

        sched_count = len(self._scheduled)
        if (sched_count and self._timer_cancelled_count):
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
                        log.warning('Executing %s took %.3f seconds', _format_handle(handle), dt)
                finally:
                    self._current_handle = None
            else:
                handle._run()
        handle = None  # Needed to break cycles when an exception occurs.

    def _check_closed(self):
        if self._closed:
            raise RuntimeError('Event loop is closed')

    def _timer_handle_cancelled(self, handle):
        """Notification that a TimerHandle has been cancelled."""
        if handle._scheduled:
            self._timer_cancelled_count += 1
