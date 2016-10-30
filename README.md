[![Build Status](https://travis-ci.org/dbrattli/aioreactive.svg?branch=master)](https://travis-ci.org/dbrattli/aioreactive)
[![Coverage Status](https://coveralls.io/repos/github/dbrattli/aioreactive/badge.svg?branch=master)](https://coveralls.io/github/dbrattli/aioreactive?branch=master)

# aioreactive - reactive tools for asyncio

Aioreactive is an asynchronous and reactive Python library for asyncio using async and await. Aioreactive is based on concepts from [RxPY](https://github.com/ReactiveX/RxPY), but is more low-level, and integrates more naturally with the Python language.

>aioreactive is the unification of reactive programming and asyncio using async and await.

## The design goals for aioreactive:

* Python 3.5+ only. We have a hard dependency on `async` and `await`.
* All operators and tools are implemented as plain old functions. No methods other than Python special methods.
* Everything is `async`. Sending values is async, listening to sources is async, even mappers or predicates may sleep or perform other async operations.
* One scheduler to rule them all. Everything runs on the asyncio base event-loop.
* No multi-threading. Only async and await with concurrency using asyncio. Threads are hard, and in many cases it doesn’t make sense to use multi-threading in Python applications. If you need to use threads you may wrap them with [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures) and compose them into the chain with `flat_map()` or similar. See [`parallel.py`](https://github.com/dbrattli/aioreactive/blob/master/examples/parallel/parallel.py) for an example.
* Simple, clean and use few abstractions. Try to align with the itertools package, and reuse as much from the Python standard library as possible.
* Support type hints and optional static type checking.
* Implicit synchronous back-pressure &trade;. Producers of events will simply be awaited until the event can be processed by the down-stream event consumers.

# Core level

At the core, aioreactive is small low-level asynchronous library for reactive programming. This core library may be used directly at the `AsyncSource` level, or one may choose to use higher level abstractions such as `Producer` or `AsyncObservable` described further down on this page.

## AsyncSource and AsyncSink

Aioreactive is built around the asynchronous duals, or opposites of the AsyncIterable and AsyncIterator abstract base classes. These async classes are called AsyncSource and AsyncSink.

AsyncSource is the dual or opposite of AsyncIterable and provides a single setter method called `__astart__()` that is the dual of the `__aiter__()` getter method:

```python
from abc import ABCMeta, abstractmethod

class AsyncSource(metaclass=ABCMeta):
    @abstractmethod
    async def __astart__(self, sink):
        return NotImplemented
```

AsyncSink is modelled after the so-called [consumer interface](http://effbot.org/zone/consumer.htm), the enhanced generator interface in [PEP-342](https://www.python.org/dev/peps/pep-0342/) and async generators in [PEP-525](https://www.python.org/dev/peps/pep-0525/). It is the dual of the AsyncIterator `__anext__()` method, and expands to three async methods `asend()`, that is the opposite of `__anext__()`, `athrow()` that is the opposite of an `raise Exception()` and `aclose()` that is the opposite of `raise StopAsyncIteration`:

```python
from abc import ABCMeta, abstractmethod

class AsyncSink(AsyncSource):
    @abstractmethod
    async def asend(self, value):
        return NotImplemented

    @abstractmethod
    async def athrow(self, error):
        return NotImplemented

    @abstractmethod
    async def aclose(self):
        return NotImplemented

    async def __astart__(self, sink):
        return self
```

Sinks are also sources. This is similar to how Iterators are also Iterables in Python. This enable us to chain sinks together. While chaining sinks is not normally done when using aioreactive, it's used extensively by the various sources and operators when you start streaming them.

## Streaming sources

A source starts streaming by using the `start()` function. The `start()` function takes a source and an optional sink, and returns a stream. If a sink is given it will receive all values that are passed through the source. So the `start()` function is used to attach a sink to the source, and start streaming values though source. The stream returned by `start()` is cancellable, iterable, and chainable. We will learn more about this later. Here is an example:

```python
async def asend(value):
    print(value)

stream = await start(source, FuncSink(asend))
```

`FuncSink` is an anonymous sink that constructs an `AsyncSink` out of plain async functions, so you don't have to implement a new named sink every time you need one.

To stop streaming you need to call the `cancel()` method.

```python
stream.cancel()
```

A stream may also be awaited. The await will resolve when the stream closes, either normally or with an error. The value returned will be the last value received through the stream. If no value has been received when the stream closes, then await will throw `CancelledError`.

```python
value = await (await start(source, FuncSink(asend)))
```

The double await can be replaced by the better looking function `run()` which basically does the same thing:

```python
value = await run(ys, FuncSink(asend))
```

Even more interresting, streams are also async iterable so you can flip around from `AsyncSource` to an `AsyncIterable` and use `async-for` to consume the stream.

```python
async with start(source) as stream:
    async for x in stream:
        print(x)
```

## Streams are also async iterables

Streams implements `AsyncIterable` so may iterate them asynchronously. They effectively transform us from an async push model to an async pull model. This enable us to use language features such as async-for. We do this without any queueing as push by the `AsyncSource` will await the pull by the `AsyncIterator.  This effectively applies so-called "back-pressure" up the stream as the source will await the iterator to pick up the sent item.

The for-loop may be wrapped with async-with may to control the lifetime of the subscription:

```python
xs = from_iterable([1, 2, 3])
result = []

async with start(xs) as ys:
    async for x in ys:
        result.append(x)

assert result == [1, 2, 3]
```

## Async streams

Aioreactive also lets you create streams directly. A stream is really just a sink and a source. The sink and the source may however be chained together though multiple operators that transforms the stream in some way.

    Source -> Operator -> Operator -> Operator -> Sink

Or they may be a single object where the object defines some semantics that the stream should ahere to.

    AsyncMuliStream or AsyncSingleStream

Since every sink is also a source, it's better described as as a sink that may be chained together with other sinks or streams. Thus the simplest form of a stream is just a single `Sink`.

    Sink

You can create streams directly from `AsyncMultiStream` or `AsyncSingleStream`. `AsyncMultiStream` supports multiple sinks, and is hot in the sense that it will drop any event if there are no sinks attached. `AsyncSingleStream` on the other hand supports a single sink, and is cold in the sense that it will await any producer until there is a sink attached.

You start streaming a stream the same was as with any other source:

```python
xs = AsyncStream()  # Alias for AsyncMultiStream

sink = FuncSink()
await start(xs, sink)
await xs.asend(42)
```

## Functions and operators

Sources and streams may be created, transformed, filtered, aggregated, or combined using operators. Operators are plain functions that you may apply to a source stream.

Aioreactive contains many of the same operators as you know from Rx. Our goal is not to implement them all, but to have the most essential onces. Other may be added by extension libraries.

* **concat** -- Concatenates two or more source streams.
* **debounce** -- Throttles a source stream.
* **delay** -- delays the items within a source stream.
* **distinct_until_changed** -- stream with continously distict values.
* **filter** -- filters a source stream.
* **flat_map** -- transforms a stream into a stream of streams and flattens the resulting stream.
* **from_iterable** -- Create a source stream from an (async) iterable.
* **listen** -- Subscribes a sink to a source. Returns a future.
* **map** -- transforms a source stream.
* **merge** -- Merges a stream of streams.
* **run** -- Awaits the future returned by listen. Returns when the subscription closes.
* **slice** -- Slices a source stream.
* **switch_latest** -- Merges the latest stream in a stream of streams.
* **unit** -- Converts a value or future to a source stream.
* **with_latest_from** -- Combines two streams.

# Functional or object-oriented, reactive or interactive

With aioreactive you can choose to program functionally with plain old functions, or object-oriented with classes and methods. There are currently two different implementations layered on top of `AsyncSource` called `Producer`and `AsyncObservable`. `Producer` is a functional reactive and interactive world, while `AsyncObservable` is an object-oriented and reactive world.

# Producer

The `Producer` is a functional world built on top of `AsyncSource`.

## Producers are composed with pipelining

`Producer` composes operators using forward pipelining with the `|` (or) operator. This works by having the operators partially applied with their arguments before being given the source stream argument.

```python
ys = xs | op.filter(predicate) | op.map(mapper) | op.flat_map(request)
```

Longer pipelines may break lines as for binary operators:

```python
from aioreactive.producer import start, op

async def main():
    stream = Stream()

    xs = (stream
          | op.map(lambda x: x["term"])
          | op.filter(lambda text: len(text) > 2)
          | op.debounce(0.75)
          | op.distinct_until_changed()
          | op.map(search_wikipedia)
          | op.switch_latest()
          )

    async with start(xs) as ys
        async for value in ys:
            print(value)
```

Producers also supports slicing using the Python slice notation.

```python
@pytest.mark.asyncio
async def test_slice_special():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, FuncSink(asend))

    assert result == 4
    assert values == [2, 3, 4]
```

# AsyncObservable

## Async observables and async observers

An alternative to `Producer` and pipelining is to use async observables and method chaining as we know from [ReactiveX](http://reactivex.io). Async Observables are almost the same as the Observables we are used to from [RxPY](https://github.com/ReactiveX/RxPY). The difference is that all methods such as `.subscribe()` and observer methods such as `on_next(value)`, `on_error(err)` and `on_completed()` are all async and needs to be awaited.

```python
@pytest.mark.asyncio
async def test_observable_simple_pipe():
    xs = AsyncObservable.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs.where(predicate).select(mapper)

    async def on_next(value):
        result.append(value)

    subscription = await ys.subscribe(AsyncAnonymousObserver(on_next))
    await subsubscription
    assert result == [20, 30]
```

# Virtual time testing

Aioreactive also provides a virtual time event loop (`VirtualTimeEventLoop`) that enables you to write asyncio unit-tests that run in virtual time. Virtual time means that time is emulated, so tests run as quickly as possible even if they sleep or awaits long lived operations. A test using virtual time still gives the same result as it would have done if it had been run in real time.

For example the following test still gives the correct result even if it takes 0 seconds to run:

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

The `aioreactive.testing` module provides a test `Stream` that may delay sending values, and test `FuncSink` that records all events. These two classes helps you with testing in virtual time.

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_delay_done():
    xs = Stream()  # Test stream

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = FuncSink()  # Test FuncSink
    sub = await start(ys, lis)
    await xs.asend_later(0, 10)
    await xs.asend_later(1, 20)
    await xs.aclose_later(1)
    await sub

    assert lis.values == [
        (0.5, 10),
        (1.5, 20),
        (2.5,)
    ]
```

# Why not use AsyncIterable for everything?

`AsyncIterable` and `AsyncSource` are closely related (in fact they are duals). `AsyncIterable` is an async iterable (pull) world, while `AsyncSource` is an async reactive (push) based world. There are many operations such as `map()` and `filter()` that may be simpler to implement using `AsyncIterable`, but once we start to include time, then `AsyncSource` really starts to shine. Operators such as `delay()` makes much more sense for `AsyncSource` than for `AsyncIterable`.

However, aioreactive makes it easy for you to flip-around to async iterable just before you need to comsume the stream, thus giving you the best of both worlds.

# Will aioreactive replace RxPY?

Aioreactive will not replace [RxPY](https://github.com/ReactiveX/RxPY). RxPY is an implementation of `Observable`. Aioreactive however lives within the `AsyncObservable` dimension.

Rx and RxPY has hundreds of different query operators, and we have no plans to implementing all of those for aioreactive.

Many ideas from aioreactive might be ported back into RxPY, and the goal is that RxPY one day may be built on top of aioreactive.

# References

Aioreactive was inspired by:

* [Is it really Pythonic to continue using linq operators instead of plain old functions?](https://github.com/ReactiveX/RxPY/issues/94)
* [Reactive Extensions (Rx)](http://reactivex.io) and [RxPY](https://github.com/ReactiveX/RxPY).
* [Dart Streams](https://www.dartlang.org/tutorials/language/streams)
* [Underscore.js](http://underscorejs.org).
* [itertools](https://docs.python.org/3/library/itertools.html) and [functools](https://docs.python.org/3/library/functools.html).
* [dbrattli/OSlash](https://github.com/dbrattli/OSlash)
* [kriskowal/q](https://github.com/kriskowal/q).

# License

The MIT License (MIT)
Copyright (c) 2016 Børge Lanes, Dag Brattli.
