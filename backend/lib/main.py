from aiohttp import web
import socketio
import baltimore_county as scraper
import multiprocessing
import asyncio

# Create the Socket.IO server
io = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
io.attach(app)

# Get the number of CPU cores
num_workers = multiprocessing.cpu_count()  # 8

# Initialize driver-related variables
drivers = []
available_drivers = []
connected_clients = set()


def get_driver():
    """Get an available driver or create a new one if none are available."""
    if available_drivers:
        print("Reusing driver")
        return available_drivers.pop()
    else:
        print("Creating new driver")
        return scraper.start_driver()


def release_driver(driver):
    """Release the driver and make it available for reuse."""
    available_drivers.append(driver)


@io.event
def connect(sid, environ):
    """Handle the connection of a new client."""
    print("connect ", sid)
    connected_clients.add(sid)


@io.event
def disconnect(sid):
    """Handle the disconnection of a client."""
    print("disconnect ", sid)
    connected_clients.remove(sid)
    drivers.clear()
    available_drivers.clear()


async def create_driver():
    """Create a new driver in an asynchronous thread."""
    return await asyncio.to_thread(scraper.start_driver)


@io.event
async def scrape_baltimore_county(sid, data):
    """
    Scrape Baltimore County for property data.

    - sid: Socket ID of the client making the request.
    - data: Data containing the addresses to scrape.

    This function performs the scraping concurrently for each address.
    """
    global drivers
    global num_workers
    addresses = data["addresses"]

    async def scrape_single_address(address):
        """Scrape the property data for a single address."""
        driver = get_driver()
        try:
            result = await asyncio.to_thread(
                scraper.scrape_baltimore_county, address, driver
            )
            if sid in connected_clients:
                await io.emit("baltimore_county_scrape_result", result, room=sid)
        except Exception as e:
            print(f"Error scraping {address}: {e}")
        finally:
            print(f"Releasing driver for {address}")
            release_driver(driver)

    tasks = []
    for address in addresses:
        tasks.append(scrape_single_address(address))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Start the web server
    web.run_app(app, port=1337)
