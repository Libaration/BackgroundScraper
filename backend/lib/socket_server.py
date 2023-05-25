import socketio
import tornado.web
import asyncio

# Create the Socket.IO server
io = socketio.AsyncServer(async_mode="tornado", cors_allowed_origins="*")


def make_app():
    return tornado.web.Application(
        [
            (r"/socket.io/", socketio.get_tornado_handler(io)),
        ],
    )


async def main():
    """Start the server."""
    app = make_app()
    app.listen(1337)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    # Start the web server
    asyncio.run(main())
