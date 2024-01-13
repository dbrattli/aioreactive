"""Example running an aiohttp server doing search queries against
Wikipedia to populate the autocomplete dropdown in the web UI. Start
using `python autocomplete.py` and navigate your web browser to
http://localhost:8080.

Requirements:
> pip3 install aiohttp
> pip3 install aiohttp_jinja2
"""
import asyncio
import json
import os
from asyncio.events import AbstractEventLoop
from typing import Any

import aiohttp
import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.http_websocket import WSMessage
from aiohttp.web_request import Request
from aiohttp.web_ws import WebSocketResponse
from expression.core import pipe

import aioreactive as rx


Msg = dict[str, str]


async def search_wikipedia(term: str) -> rx.AsyncObservable[str]:
    """Search Wikipedia for a given term"""
    url = "http://en.wikipedia.org/w/api.php"

    params = {"action": "opensearch", "search": term, "format": "json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            json_response = await resp.text()
            return rx.single(json_response)


async def websocket_handler(request: Request) -> WebSocketResponse:
    print("WebSocket opened")

    stream: rx.AsyncObservable[Msg] = rx.AsyncSubject()

    def mapper(x: Msg) -> str:
        return x["term"]

    xs = pipe(
        stream,
        rx.map(mapper),
        rx.filter(lambda text: len(text) > 2),
        rx.debounce(0.5),
        rx.distinct_until_changed,
        rx.flat_map_async(search_wikipedia),
    )

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def asend(value: str) -> None:
        print("asend: ", value)
        await ws.send_str(value)

    async def athrow(ex: Exception) -> None:
        print(ex)

    await xs.subscribe_async(rx.AsyncAnonymousObserver(asend, athrow))

    async for msg in ws:
        msg: WSMessage
        if msg.type == aiohttp.WSMsgType.TEXT:
            obj = json.loads(msg.data)
            await stream.asend(obj)

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with exception %s" % ws.exception())

    print("websocket connection closed")
    return ws


@aiohttp_jinja2.template("index.html")
async def index(request: Request) -> dict[str, Any]:
    return dict()


async def init(loop: AbstractEventLoop):
    port = os.environ.get("PORT", 8080)
    host = "localhost"
    app = web.Application(loop=loop)
    print("Starting server at port: %s" % port)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("."))
    app.router.add_static("/static", "static")
    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket_handler)

    return app, host, port


def main():
    loop: AbstractEventLoop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=int(port))


if __name__ == "__main__":
    main()
