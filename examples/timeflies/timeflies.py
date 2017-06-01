import asyncio
from tkinter import *

from aioreactive.core import subscribe, AsyncAnonymousObserver
from aioreactive.core import AsyncStream
from aioreactive.operators.pipe import delay


async def main(loop) -> None:
    root = Tk()
    root.title("aioreactive")

    mousemoves = AsyncStream()

    frame = Frame(root, width=800, height=600)

    async def move(event) -> None:
        await mousemoves.asend(event)

    def call_move(event):
        asyncio.ensure_future(move(event))
    frame.bind("<Motion>", call_move)

    text = "HACKATHON 2017 - MAKE EPIC STUFF"
    labels = [Label(frame, text=c) for c in text]

    async def handle_label(i, label) -> None:
        label.config(dict(borderwidth=0, padx=0, pady=0))

        async def asend(ev) -> None:
            label.place(x=ev.x + i * 12 + 15, y=ev.y)

        await (mousemoves | delay(i / 10.0) > AsyncAnonymousObserver(asend))

    for i, label in enumerate(labels):
        await handle_label(i, label)

    frame.pack()

    # A simple combined event loop
    while True:
        root.update()
        await asyncio.sleep(0.005)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
