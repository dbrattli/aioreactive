
<img src="logo/logo.jpg" alt="drawing" width="200"/>

# aioreactive - ReactiveX for asyncio using async and await
[![PyPI](https://img.shields.io/pypi/v/aioreactive.svg)](https://pypi.python.org/pypi/aioreactive)
![Python package](https://github.com/dbrattli/aioreactive/workflows/Python%20package/badge.svg)
![Upload Python Package](https://github.com/dbrattli/aioreactive/workflows/Upload%20Python%20Package/badge.svg)
[![codecov](https://codecov.io/gh/dbrattli/aioreactive/branch/master/graph/badge.svg)](https://codecov.io/gh/dbrattli/aioreactive)


> *NEWS: Project rebooted Nov. 2020. Rebuilt using [Expression](https://github.com/dbrattli/Expression).*

Aioreactive is [RxPY](https://github.com/ReactiveX/RxPY) for asyncio.
It's an asynchronous and reactive Python library for asyncio using async
and await. Aioreactive is built on the
[Expression](https://github.com/dbrattli/Expression) functional library
and, integrates naturally with the Python language.

> aioreactive is the unification of RxPY and reactive programming with
> asyncio using async and await.

## The design goals for aioreactive:

* Python 3.9+ only. We have a hard dependency [PEP
  585](https://www.python.org/dev/peps/pep-0585/), Type Hinting Generics
  In Standard Collections, data classes and type variables.
* All operators and tools are implemented as plain old functions.
* Everything is `async`. Sending values is async, subscribing to
  observables is async. Disposing subscriptions is async.
* One scheduler to rule them all. Everything runs on the asyncio base
  event-loop.
* No multi-threading. Only async and await with concurrency using
  asyncio. Threads are hard, and in many cases it doesn’t make sense to
  use multi-threading in Python applications. If you need to use threads
  you may wrap them with
  [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures)
  and compose them into the chain with `flat_map()` or similar. See
  [`parallel.py`](https://github.com/dbrattli/aioreactive/blob/master/examples/parallel/parallel.py)
  for an example.
* Simple, clean and use few abstractions. Try to align with the
  itertools package, and reuse as much from the Python standard library
  as possible.
* Support type hints and static type checking using [Pylance](https://devblogs.microsoft.com/python/announcing-pylance-fast-feature-rich-language-support-for-python-in-visual-studio-code/).
* Implicit synchronous back-pressure &trade;. Producers of events will
  simply be awaited until the event can be processed by the down-stream
  consumers.

## AsyncObservable and AsyncObserver

With aioreactive you subscribe observers to observables, and the key
abstractions of aioreactive can be seen in this single line of code:

```python
subscription = await observable.subscribe_async(observer)
```

The difference from RxPY can be seen with the `await` expression.
Aioreactive is built around the asynchronous duals, or opposites of the
AsyncIterable and AsyncIterator abstract base classes. These async
classes are called AsyncObservable and AsyncObserver.

AsyncObservable is a producer of events. It may be seen as the dual or
opposite of AsyncIterable and provides a single setter method called
`subscribe_async()` that is the dual of the `__aiter__()` getter method:

```python
from abc import ABC, abstractmethod

class AsyncObservable(ABC):
    @abstractmethod
    async def subscribe_async(self, observer):
        return NotImplemented
```

AsyncObserver is a consumer of events and is modeled after the
so-called [consumer interface](http://effbot.org/zone/consumer.htm), the
enhanced generator interface in
[PEP-342](https://www.python.org/dev/peps/pep-0342/) and async
generators in [PEP-525](https://www.python.org/dev/peps/pep-0525/). It
is the dual of the AsyncIterator `__anext__()` method, and expands to
three async methods `asend()`, that is the opposite of `__anext__()`,
`athrow()` that is the opposite of an `raise Exception()` and `aclose()`
that is the opposite of `raise StopAsyncIteration`:

```python
from abc import ABC, abstractmethod

class AsyncObserver(ABC):
    @abstractmethod
    async def asend(self, value):
        return NotImplemented

    @abstractmethod
    async def athrow(self, error):
        return NotImplemented

    @abstractmethod
    async def aclose(self):
        return NotImplemented
```

## Subscribing to observables

An observable becomes hot and starts streaming items by using the
`subscribe_async()` method. The `subscribe_async()` method takes an
observable and returns a disposable subscription. So the
`subscribe_async()` method is used to attach a observer to the
observable.

```python
async def asend(value):
    print(value)

disposable = await subscribe(source, AsyncAnonymousObserver(asend))
```

`AsyncAnonymousObserver` is an anonymous observer that constructs an
`AsyncObserver` out of plain async functions, so you don't have to
implement a new named observer every time you need one.

The subscription returned by `subscribe_async()` is disposable, so to
unsubscribe you need to await the `dispose_async()` method on the
subscription.

```python
await subscription.dispose_async()
```

## Asynchronous iteration

Even more interesting, with `to_async_iterable` you can flip around from
`AsyncObservable` to an `AsyncIterable` and use `async-for` to consume
the stream of events.

```python
obv = AsyncIteratorObserver()
subscription = subscribe(source, obv)
async for x in obv:
    print(x)
```

They effectively transform us from an async push model to an async pull
model, and lets us use the awesome new language features such as `async
for` and `async-with`. We do this without any queueing, as a push by the
`AsyncObservable` will await the pull by the `AsyncIterator.  This
effectively applies so-called "back-pressure" up the subscription as the
producer will await the iterator to pick up the item send.

The for-loop may be wrapped with async-with to control the lifetime of
the subscription:

```python
import aioreactive as rx

xs = rx.from_iterable([1, 2, 3])
result = []

obv = rx.AsyncIteratorObserver()
async with await xs.subscribe(obv) as subscription:
    async for x in obv:
        result.append(x)

assert result == [1, 2, 3]
```

## Async streams

An async stream is both an async observer and an async observable.
Aioreactive lets you create streams explicitly.

```python
import aioreactive as rx

stream = AsyncSubject()  # Alias for AsyncMultiStream

sink = rx.AsyncAnonymousObserver()
await stream.subscribe_async(sink)
await stream.asend(42)
```

You can create streams directly from `AsyncMultiStream` or
`AsyncSingleStream`. `AsyncMultiStream` supports multiple observers, and
is hot in the sense that it will drop any event that is sent if there
are currently no observers attached. `AsyncSingleStream` on the other
hand supports a single observer, and is cold in the sense that it will
await any producer until there is an observer attached.

## Operators

The Rx operators in aioreactive are all plain old functions. You can
apply them to an observable and compose it into a transformed, filtered,
aggregated or combined observable. This transformed observable can be
streamed into an observer.

    Observable -> Operator -> Operator -> Operator -> Observer

Aioreactive contains many of the same operators as you know from RxPY.
Our goal is not to implement them all, but to provide the most essential
ones.

* **concat** -- Concatenates two or more observables.
* **choose** -- Filters and/or transforms the observable.
* **choose_asnc** -- Asynchronously filters and/or transforms the observable.
* **debounce** -- Throttles an observable.
* **delay** -- delays the items within an observable.
* **distinct_until_changed** -- an observable with continuously distinct values.
* **filter** -- filters an observable.
* **filteri** -- filters an observable with index.
* **flat_map** -- transforms an observable into a stream of observables and flattens the resulting observable.
* **flat_map_latest** -- transforms an observable into a stream of
  observables and flattens the resulting observable by producing values
  from the latest observable.
* **from_iterable** -- Create an observable from an (async) iterable.
* **subscribe** -- Subscribes an observer to an observable. Returns a subscription.
* **map** -- transforms an observable.
* **mapi** -- transforms an observable with index.
* **map_async** -- transforms an observable asynchronously.
* **mapi_async** -- transforms an observable asynchronously with index.
* **merge_inner** -- Merges an observable of observables.
* **merge** -- Merge one observable with another observable.
* **merge_seq** -- Merge a sequence of observables.
* **run** -- Awaits the future returned by subscribe. Returns when the subscription closes.
* **slice** -- Slices an observable.
* **skip** -- Skip items from the start of the observable stream.
* **skip_last** -- Skip items from the end of the observable stream.
* **starfilter** -- Filters an observable with a predicate and spreads the arguments.
* **starmap** -- Transforms and async observable and spreads the arguments to the mapper.
* **switch_latest** -- Merges the latest stream in an observable of streams.
* **take** -- Take a number of items from the start of the observable stream.
* **take_last** -- Take a number of items from the end of the observable stream.
* **unit** -- Converts a value or future to an observable.
* **with_latest_from** -- Combines two observables into one.

# Functional or object-oriented, reactive or interactive

With aioreactive you can choose to program functionally with plain old
functions, or object-oriented with classes and methods. Aioreactive
supports both method chaining or forward pipe programming styles.

## Pipe forward programming style

`AsyncObservable` may compose operators using forward pipelining with
the `pipe` operator provided by the amazing
[Expression](https://github.com/dbrattli/Expression) library. This works
by having the operators partially applied with their arguments before
being given the source stream as the last curried argument.

```python
ys = pipe(xs, filter(predicate), map(mapper), flat_map(request))
```

Longer pipelines may break lines as for binary operators:

```python
import aioreactve as rx

async def main():
    stream = rx.AsyncSubject()
    obv = rx.AsyncIteratorObserver()

    xs = pipe(
        stream,
        rx.map(lambda x: x["term"]),
        rx.filter(lambda text: len(text) > 2),
        rx.debounce(0.75),
        rx.distinct_until_changed(),
        rx.map(search_wikipedia),
        rx.switch_latest(),
    )

    async with xs.subscribe(obv) as ys
        async for value in obv:
            print(value)
```

AsyncObservable also supports slicing using the Python slice notation.

```python
@pytest.mark.asyncio
async def test_slice_special():
    xs = rx.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, AsyncAnonymousObserver(asend))

    assert result == 4
    assert values == [2, 3, 4]
```

# Fluent and chained programming style

An alternative to pipelining is to use the classic and fluent method
chaining as we know from [ReactiveX](http://reactivex.io).

An `AsyncObservable` created from class methods such as
`AsyncRx.from_iterable()` returns a `AsyncChainedObservable`.
where we may use methods such as `.filter()` and `.map()`.

```python
from aioreactive import AsyncRx

@pytest.mark.asyncio
async def test_observable_simple_pipe():
    xs = AsyncRx.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs.filter(predicate).map(mapper)

    async def on_next(value):
        result.append(value)

    subscription = await ys.subscribe(AsyncAnonymousObserver(on_next))
    await subsubscription
    assert result == [20, 30]
```

# Virtual time testing

Aioreactive also provides a virtual time event loop
(`VirtualTimeEventLoop`) that enables you to write asyncio unit-tests
that run in virtual time. Virtual time means that time is emulated, so
tests run as quickly as possible even if they sleep or awaits long-lived
operations. A test using virtual time still gives the same result as it
would have done if it had been run in real-time.

For example the following test still gives the correct result even if it
takes 0 seconds to run:

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_call_later():
    result = []

    def action(value):
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]
```

The aioreactive testing module provides a test `AsyncSubject` that may
delay sending values, and a test `AsyncTestObserver` that records all
events. These two classes helps you with testing in virtual time.

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_delay_done():
    xs = AsyncSubject()  # Test stream

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = AsyncTestObserver()  # Test AsyncAnonymousObserver
    sub = await subscribe(ys, lis)
    await xs.asend_later(0, 10)
    await xs.asend_later(1, 20)
    await xs.aclose_later(1)
    await sub

    assert lis.values == [
        (0.5, OnNext(10)),
        (1.5, OnNext(20)),
        (2.5, OnCompleted)
    ]
```

# Why not use AsyncIterable for everything?

`AsyncIterable` and `AsyncObservable` are closely related (in fact they
are duals). `AsyncIterable` is an async iterable (pull) world, while
`AsyncObservable` is an async reactive (push) based world. There are
many operations such as `map()` and `filter()` that may be simpler to
implement using `AsyncIterable`, but once we start to include time, then
`AsyncObservable` really starts to shine. Operators such as `delay()`
makes much more sense for `AsyncObservable` than for `AsyncIterable`.

However, aioreactive makes it easy for you to flip-around to async
iterable just before you need to consume the stream, thus giving you the
best of both worlds.

# Will aioreactive replace RxPY?

Aioreactive will not replace [RxPY](https://github.com/ReactiveX/RxPY).
RxPY is an implementation of `Observable`. Aioreactive is an
implementation of `AsyncObservable`.

Rx and RxPY has hundreds of different query operators, and we currently
have no plans to implementing all of them for aioreactive.

Many ideas from aioreactive have already been ported back into "classic" RxPY.

# References

Aioreactive was inspired by:

* [AsyncRx](https://github.com/dbrattli/asyncrx) - Aioreactive is a direct port of AsyncRx from F#.
* [Expression](https://github.com/dbrattli/Expression) - Functional programming for Python.
* [Is it really Pythonic to continue using LINQ operators instead of plain old functions?](https://github.com/ReactiveX/RxPY/issues/94)
* [Reactive Extensions (Rx)](http://reactivex.io) and [RxPY](https://github.com/ReactiveX/RxPY).
* [Dart Streams](https://www.dartlang.org/tutorials/language/streams)
* [Underscore.js](http://underscorejs.org).
* [itertools](https://docs.python.org/3/library/itertools.html) and [functools](https://docs.python.org/3/library/functools.html).
* [dbrattli/OSlash](https://github.com/dbrattli/OSlash)
* [kriskowal/q](https://github.com/kriskowal/q).

# License

The MIT License (MIT)
Copyright (c) 2016 Børge Lanes, Dag Brattli.
