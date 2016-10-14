import asyncio
from tkinter import *

from aioreactive.core import listen, Listener
from aioreactive.producer import Stream
from aioreactive.producer import op


async def main(loop):
    root = Tk()
    root.title("aioreactive rocks")

    mousemoves = Stream()

    frame = Frame(root, width=600, height=600)

    async def move(event):
        await mousemoves.asend(event)

    def call_move(event):
        asyncio.ensure_future(move(event))
    frame.bind("<Motion>", call_move)

    text = 'TIME FLIES LIKE AN ARROW'
    labels = [Label(frame, text=c) for c in text]

    async def handle_label(i, label):
        label.config(dict(borderwidth=0, padx=0, pady=0))

        def asend(ev):
            label.place(x=ev.x + i * 12 + 15, y=ev.y)

        xs = mousemoves | op.delay(i / 10.0)
        await listen(xs, Listener(asend))

    for i, label in enumerate(labels):
        await handle_label(i, label)

    frame.pack()

    # A simple combined event loop
    while True:
        root.update()
        await asyncio.sleep(0.01)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
