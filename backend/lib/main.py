from aiohttp import web
from logger import log
from driver import get_driver, release_driver, available_drivers
from baltimore_county import baltimore_find_account_id_and_scrape
import socketio
import tornado

# Initialize variables
connected_clients = set()
# Create the Socket.IO server
io = socketio.AsyncServer(async_mode="tornado", cors_allowed_origins="*")
app = tornado.web.Application(
    [
        (r"/socket.io/", socketio.get_tornado_handler(io)),
    ],
)


@io.event
def connect(sid, environ):
    """Handle the connection of a new client."""
    log("info", f"New client connected: {sid}")
    connected_clients.add(sid)


@io.event
def disconnect(sid):
    """Handle the disconnection of a client."""
    log("error", f"Client disconnected: {sid}")
    connected_clients.remove(sid)
    available_drivers.clear()


async def scrape_single_address(address, sid):
    """Scrape the property data for a single address."""
    driver = get_driver()
    try:
        result = await baltimore_find_account_id_and_scrape(address, driver)
        if result is not None:
            log("success", f"Retrieved data for address {address}")
            log("debug", f"Socket ID: {sid}")
            log("debug", f"Connected clients: {connected_clients}")
            if sid in connected_clients:
                return {"address": address, "result": result}
    except Exception as e:
        log("error", f"Error scraping {address}: {e}")
    finally:
        log("debug", f"Releasing driver for {address}")
        release_driver(driver)


@io.event
async def scrape_baltimore_county(sid, data):
    """
    Scrape Baltimore County for property data.

    - sid: Socket ID of the client making the request.
    - data: Data containing the addresses to scrape.

    This function performs the scraping concurrently for each address.
    """
    addresses = data["addresses"]

    async def emit_result(result):
        await io.emit("baltimore_county_scrape_result", result, room=sid)
        log("success", f"Sent result: {result}")

    async def process_addresses():
        for address in addresses:
            log("info", f"Scraping data for address {address}")
            result = await scrape_single_address(address, sid)
            if result is not None:
                await emit_result(result)

    await process_addresses()


if __name__ == "__main__":
    # Start the web server
    app.listen(1337)
    tornado.ioloop.IOLoop.current().start()
