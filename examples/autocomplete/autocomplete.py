"""
Example running an aiohttp server doing search queries against
Wikipedia to populate the autocomplete dropdown in the web UI. Start
using `python autocomplete.py` and navigate your web browser to
http://localhost:8080

Requirements:
> pip3 install aiohttp
> pip3 install aiohttp_jinja2
"""

import os
import json
import asyncio

import aiohttp
import jinja2
import aiohttp_jinja2
from aiohttp import web

from aioreactive.core import AsyncAnonymousObserver, subscribe
from aioreactive.core import AsyncObservable, AsyncStream
from aioreactive.operators import pipe as op


async def search_wikipedia(term):
    """Search Wikipedia for a given term"""
    url = 'http://en.wikipedia.org/w/api.php'

    params = {
        "action": 'opensearch',
        "search": term,
        "format": 'json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return AsyncObservable.unit(await resp.text())


async def websocket_handler(request):
    print("WebSocket opened")

    stream = AsyncStream()

    # Line break before binary operator is more readable. Disable W503
    xs = (stream
          | op.map(lambda x: x["term"])
          | op.filter(lambda text: len(text) > 2)
          | op.debounce(0.75)
          | op.distinct_until_changed()
          | op.flat_map(search_wikipedia)
          #| op.switch_latest()
          )

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def asend(value):
        ws.send_str(value)

    async def athrow(ex):
        print(ex)

    await subscribe(xs, AsyncAnonymousObserver(asend, athrow))

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            obj = json.loads(msg.data)
            await stream.asend(obj)

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    print('websocket connection closed')
    return ws


@aiohttp_jinja2.template('index.html')
async def index(request):
    return dict()


async def init(loop):
    port = os.environ.get("PORT", 8080)
    host = "localhost"
    app = web.Application(loop=loop)
    print("Starting server at port: %s" % port)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))
    app.router.add_static('/static', "static")
    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)

    return app, host, port


def main():
    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
