from aiohttp import web
import socketio
import baltimore_county as scraper
import multiprocessing
import asyncio

io = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
io.attach(app)
num_workers = multiprocessing.cpu_count()  # 8
drivers = []
available_drivers = []


def get_driver():
    if available_drivers:
        print("Reusing driver")
        return available_drivers.pop()
    else:
        print("Creating new driver")
        return scraper.start_driver()


def release_driver(driver):
    available_drivers.append(driver)


@io.event
def connect(sid, environ):
    print("connect ", sid)


@io.event
def disconnect(sid):
    print("disconnect ", sid)
    drivers.clear()
    available_drivers.clear()


async def create_drivers(num_drivers):
    new_drivers = []
    for _ in range(num_drivers):
        new_driver = await asyncio.to_thread(scraper.start_driver)
        new_drivers.append(new_driver)
    return new_drivers


@io.event
async def scrape_baltimore_county(sid, data):
    global drivers
    global num_workers
    addresses = data["addresses"]
    results = []

    # Calculate the number of drivers needed
    num_addresses = len(addresses)
    num_drivers = min(num_addresses, num_workers)

    # Check if the number of drivers in the list matches the required number
    if len(drivers) < num_drivers:
        # Create additional drivers
        new_drivers = await create_drivers(num_drivers - len(drivers))
        drivers.extend(new_drivers)
        available_drivers.extend(new_drivers)

    # Loop over the list of addresses and scrape each one individually
    for address in addresses:
        driver = get_driver()
        try:
            # use with statement to ensure driver is closed even if an exception occurs

            result = await asyncio.to_thread(
                scraper.scrape_baltimore_county, address, driver
            )
            await io.emit("baltimore_county_scrape_result", result)
        except Exception as e:
            print(f"Error scraping {address}: {e}")
        finally:
            # release the driver back to the pool
            print(f"Releasing driver for {address}")
            release_driver(driver)

    # await io.emit("baltimore_county_scrape_results", results)


if __name__ == "__main__":
    web.run_app(app, port=1337)
