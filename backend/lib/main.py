from logger import log
from driver import get_driver, clear_driver_queue, start_driver
from baltimore_county import baltimore_find_account_id_and_scrape
from socket_server import io, main
import asyncio


# Initialize variables
connected_clients = set()


async def scrape_single_address(address, sid):
    """Scrape the property data for a single address."""
    driver = await get_driver()
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
    clear_driver_queue()


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
        log("success", f"Sent result for address {result['address']}")

    async def process_addresses():
        for address in addresses:
            log("info", f"Scraping data for address {address}")
            result = await scrape_single_address(address, sid)
            if result is not None:
                await emit_result(result)

    await process_addresses()


if __name__ == "__main__":
    # Start the web server
    # async def main_async():
    #     await asyncio.gather(main(), start_driver())

    # asyncio.run(main_async())
    asyncio.run(main())
