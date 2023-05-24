from aiohttp import web
import socketio
import baltimore_county as scraper
import multiprocessing
import asyncio
import threading
import datetime


# Create the Socket.IO server
io = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
io.attach(app)

# Get the number of CPU cores
num_workers = multiprocessing.cpu_count()  # 8

# Initialize driver-related variables
available_drivers = []
connected_clients = set()
driver_lock = threading.Lock()


def log(*args):
    """Log a message with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    msg = " ".join(str(arg) for arg in args)
    print(f"[{timestamp}] {msg}")


def get_driver():
    log("Available drivers:", len(available_drivers))
    log(available_drivers)
    print("-" * 50)
    """Get an available driver or create a new one if none are available."""
    with driver_lock:
        if available_drivers:
            log("Reusing driver")
            return available_drivers.pop()
        else:
            log("Creating new driver")
            driver = scraper.start_driver()
            log(f"New driver created: {driver}")
            return driver


def release_driver(driver):
    """Release the driver and make it available for reuse."""
    with driver_lock:
        available_drivers.append(driver)
        log(f"Driver released: {driver}")


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
            print(f"Result for {address}: {result}")
            print("sid ", sid)
            print("connected_clients ", connected_clients)
            if sid in connected_clients:
                await io.emit("baltimore_county_scrape_result", result, room=sid)
                print(f"Sent result for {address}")
        except Exception as e:
            print(f"Error scraping {address}: {e}")
        finally:
            print(f"Releasing driver for {address}")

    tasks = []
    for address in addresses:
        tasks.append(scrape_single_address(address))

    await asyncio.gather(*tasks)

    # Release the drivers after all tasks are completed
    for address in addresses:
        driver = get_driver()
        release_driver(driver)


if __name__ == "__main__":
    # Start the web server
    web.run_app(app, port=1337)
