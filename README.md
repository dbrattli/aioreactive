[![Build Status](https://travis-ci.org/dbrattli/aioreactive.svg?branch=master)](https://travis-ci.org/dbrattli/aioreactive)
[![Coverage Status](https://coveralls.io/repos/github/dbrattli/aioreactive/badge.svg?branch=master)](https://coveralls.io/github/dbrattli/aioreactive?branch=master)

# aioreactive - RxPY for asyncio using async and await

Aioreactive is [RxPY](https://github.com/ReactiveX/RxPY) for asyncio. It's an asynchronous and reactive Python library for asyncio using async and await. Aioreactive is the next version of [RxPY](https://github.com/ReactiveX/RxPY), that integrates more naturally with the Python language.

>aioreactive is the unification of RxPY, reactive programming with asyncio using async and await.

## The design goals for aioreactive:

* Python 3.5+ only. We have a hard dependency on `async` and `await`.
* All operators and tools are implemented as plain old functions. No methods other than Python special methods.
* Everything is `async`. Sending values is async, subscribing to observables is async.
* One scheduler to rule them all. Everything runs on the asyncio base event-loop.
* No multi-threading. Only async and await with concurrency using asyncio. Threads are hard, and in many cases it doesn’t make sense to use multi-threading in Python applications. If you need to use threads you may wrap them with [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures) and compose them into the chain with `flat_map()` or similar. See [`parallel.py`](https://github.com/dbrattli/aioreactive/blob/master/examples/parallel/parallel.py) for an example.
* Simple, clean and use few abstractions. Try to align with the itertools package, and reuse as much from the Python standard library as possible.
* Support type hints and optional static type checking.
* Implicit synchronous back-pressure &trade;. Producers of events will simply be awaited until the event can be processed by the down-stream consumers.

## AsyncObservable and AsyncObserver

With aioreactive you subscribe observers to observables, and the key abstractions of aioreactive can be seen in this single line of code:

```python
subscription = await subscribe(observable, observer)
```

The difference from RxPY can be seen with the `await` expression. Aioreactive is built around the asynchronous duals, or opposites of the AsyncIterable and AsyncIterator abstract base classes. These async classes are called AsyncObservable and AsyncObserver.

AsyncObservable is a producer of events. It may be seen as the dual or opposite of AsyncIterable and provides a single setter method called `__asubscribe__()` that is the dual of the `__aiter__()` getter method:

```python
from abc import ABCMeta, abstractmethod

class AsyncObservable(metaclass=ABCMeta):
    @abstractmethod
    async def __asubscribe__(self, sink):
        return NotImplemented
```

AsyncObserver is a consumer of events and is modelled after the so-called [consumer interface](http://effbot.org/zone/consumer.htm), the enhanced generator interface in [PEP-342](https://www.python.org/dev/peps/pep-0342/) and async generators in [PEP-525](https://www.python.org/dev/peps/pep-0525/). It is the dual of the AsyncIterator `__anext__()` method, and expands to three async methods `asend()`, that is the opposite of `__anext__()`, `athrow()` that is the opposite of an `raise Exception()` and `aclose()` that is the opposite of `raise StopAsyncIteration`:

```python
from abc import ABCMeta, abstractmethod

class AsyncObserver(AsyncObservable):
    @abstractmethod
    async def asend(self, value):
        return NotImplemented

    @abstractmethod
    async def athrow(self, error):
        return NotImplemented

    @abstractmethod
    async def aclose(self):
        return NotImplemented

    async def __asubscribe__(self, sink):
        return self
```

Obsevers are also Observables. This is similar to how Iterators are also Iterables in Python. This enable us to chain observers together. While chaining observers is not normally done when using aioreactive, it's used extensively by the various operators when you subscribe them.

## Subscribing to observables

An observable becomes hot and starts streaming items by using the `subscribe()` function. The `subscribe()` function takes an observable and an optional observer, and returns a subscription. If an observer is given it will receive all values that are passed through the observable. So the `subscribe()` function is used to attach a observer to the observable.

The subscription returned by `subscribe()` is cancellable, iterable, and chainable. We will learn more about this later. Here is an example:

```python
async def asend(value):
    print(value)

subscription = await subscribe(source, AsyncAnonymousObserver(asend))
```

`AsyncAnonymousObserver` is an anonymous observer that constructs an `AsyncObserver` out of plain async functions, so you don't have to implement a new named observer every time you need one.

To unsubscribe you need to call the `dispose()` method on the subscription.

```python
subscription.dispose()
```

A subscription may also be awaited. The await will resolve when the subscription ends, either normally or with an error. The returned value will be the last value received through the subscription. If no value has been received when the subscription ends, then await will throw `CancelledError`.

```python
value = await (await subscribe(source, AsyncAnonymousObserver(asend)))
```

The double await can be replaced by the better looking function `run()` which basically does the same thing. This will run the subscription to completion before returning:

```python
value = await run(ys, AsyncAnonymousObserver(asend))
```

## Subscriptions may be iterated asynchronously

Even more interresting, subscriptions are also async iterables so you can flip around from `AsyncObservable` to an `AsyncIterable` and use `async-for` to consume the stream of events.

```python
subscription = subscribe(source)
async for x in subscription:
    print(x)
```

They effectively transform us from an async push model to an async pull model, and lets us use the awsome new language features such as `async for` and `async-with`. We do this without any queueing as push by the `AsyncObservable` will await the pull by the `AsyncIterator.  This effectively applies so-called "back-pressure" up the subscription as the producer will await the iterator to pick up the item send.

The for-loop may be wrapped with async-with to control the lifetime of the subscription:

```python
xs = from_iterable([1, 2, 3])
result = []

async with subscribe(xs) as subscription:
    async for x in subscription:
        result.append(x)

assert result == [1, 2, 3]
```

## Async streams

Aioreactive also lets you create streams explicitly.

```python
stream = AsyncStream()  # Alias for AsyncMultiStream

sink = AsyncAnonymousObserver()
await subscribe(stream, sink)
await stream.asend(42)
```

You can create streams directly from `AsyncMultiStream` or `AsyncSingleStream`. `AsyncMultiStream` supports multiple observers, and is hot in the sense that it will drop any event that is sent if there are currently no observers attached. `AsyncSingleStream` on the other hand supports a single observer, and is cold in the sense that it will await any producer until there is an observer attached.

## Operators

The Rx operators in aioreactive are all plain old functions. You can apply them to an observable and compose it into a transformed, filtered, aggregated or combined observable. This transformed observable can be streamed into an observer.

    Observable -> Operator -> Operator -> Operator -> Observer

Aioreactive contains many of the same operators as you know from RxPY. Our goal is not to implement them all, but to have the most essential onces.

* **concat** -- Concatenates two or more observables.
* **debounce** -- Throttles an observable.
* **delay** -- delays the items within an observable.
* **distinct_until_changed** -- an observable with continously distict values.
* **filter** -- filters an observable.
* **flat_map** -- transforms an observable into a stream of observables and flattens the resulting observable.
* **from_iterable** -- Create an observable from an (async) iterable.
* **subscribe** -- Subscribes an observer to an observable. Returns a subscription.
* **map** -- transforms an observable.
* **merge** -- Merges an observable of observables.
* **run** -- Awaits the future returned by subscribe. Returns when the subscription closes.
* **slice** -- Slices an observable.
* **switch_latest** -- Merges the latest stream in an observable of streams.
* **unit** -- Converts a value or future to an observable.
* **with_latest_from** -- Combines two observables into one.

# Functional or object-oriented, reactive or interactive

With aioreactive you can choose to program functionally with plain old functions, or object-oriented with classes and methods. Aioreactive supports both method chaining or forward pipe programming styles.

## Pipe forward programming style

`AsyncObservable` may compose operators using forward pipelining with the `|` (or) operator. This works by having the operators partially applied with their arguments before being given the source stream argument.

```python
ys = xs | op.filter(predicate) | op.map(mapper) | op.flat_map(request)
```

Longer pipelines may break lines as for binary operators:

```python
from aioreactive.core import AsyncStream, subscribe
from aioreactive.operators import pipe as op

async def main():
    stream = AsyncStream()

    xs = (stream
          | op.map(lambda x: x["term"])
          | op.filter(lambda text: len(text) > 2)
          | op.debounce(0.75)
          | op.distinct_until_changed()
          | op.map(search_wikipedia)
          | op.switch_latest()
          )

    async with subscribe(xs) as ys
        async for value in ys:
            print(value)
```

AsyncObservable also supports slicing using the Python slice notation.

```python
@pytest.mark.asyncio
async def test_slice_special():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, AsyncAnonymousObserver(asend))

    assert result == 4
    assert values == [2, 3, 4]
```

# Fluent and chained programming style

An alternative to pipelining is to use classic and fluent method chaining as we know from [ReactiveX](http://reactivex.io).

Note the difference from RxPY, that we need to call the `chain()` function on an `AsyncObservable ` to get a `ChainedAsyncObservable`. Once we have a `ChainedAsyncObservable` we may use methods such as `.where()` and `.select()`.

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

    ys = chain(xs).where(predicate).select(mapper)

    async def on_next(value):
        result.append(value)

    subscription = await ys.subscribe(AsyncAsyncAnonymousObserver(on_next))
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

The `aioreactive.testing` module provides a test `AsyncStream` that may delay sending values, and test `AsyncAnonymousObserver` that records all events. These two classes helps you with testing in virtual time.

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_delay_done():
    xs = AsyncStream()  # Test stream

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = AsyncAnonymousObserver()  # Test AsyncAnonymousObserver
    sub = await subscribe(ys, lis)
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

`AsyncIterable` and `AsyncObservable` are closely related (in fact they are duals). `AsyncIterable` is an async iterable (pull) world, while `AsyncObservable` is an async reactive (push) based world. There are many operations such as `map()` and `filter()` that may be simpler to implement using `AsyncIterable`, but once we start to include time, then `AsyncObservable` really starts to shine. Operators such as `delay()` makes much more sense for `AsyncObservable` than for `AsyncIterable`.

However, aioreactive makes it easy for you to flip-around to async iterable just before you need to comsume the stream, thus giving you the best of both worlds.

# Will aioreactive replace RxPY?

Aioreactive will not replace [RxPY](https://github.com/ReactiveX/RxPY). RxPY is an implementation of `Observable`. Aioreactive however is an implementation of `AsyncObservable`.

Rx and RxPY has hundreds of different query operators, and we currently have no plans to implementing all of them for aioreactive.

Many ideas from aioreactive might be ported back into "classic" RxPY.

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
