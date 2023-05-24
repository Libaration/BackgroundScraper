from aiohttp import web
import socketio
import baltimore_county as scraper
import multiprocessing

io = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
io.attach(app)
num_workers = 2  # multiprocessing.cpu_count()
drivers = []


def scrape_address(args):
    address, driver_index = args
    driver = drivers[driver_index]  # Get the appropriate driver from the drivers list
    result = scraper.scrape_baltimore_county(address, driver)
    return result


@io.event
def connect(sid, environ):
    print("connect ", sid)


@io.event
async def scrape_baltimore_county(sid, data):
    addresses = data["addresses"]
    results = []

    # Calculate the number of drivers needed
    num_addresses = len(addresses)
    num_drivers = min(num_addresses, num_workers)

    # Check if the number of drivers in the list matches the required number
    if len(drivers) < num_drivers:
        # Create additional drivers
        for _ in range(num_drivers - len(drivers)):
            new_driver = scraper.start_driver()
            drivers.append(new_driver)

    if num_addresses > 1:
        # Create a list of tuples where each tuple contains an address and the corresponding driver index
        address_driver_pairs = [
            (address, i % num_drivers) for i, address in enumerate(addresses)
        ]

        with multiprocessing.Pool(num_drivers) as pool:
            results = pool.map(scrape_address, address_driver_pairs)
    else:
        # Only one address, use the first driver
        driver = drivers[0]
        result = scraper.scrape_baltimore_county(addresses[0], driver)
        results.append(result)

    return results


@io.event
def disconnect(sid):
    # Quit all the drivers in the drivers list
    for driver in drivers:
        driver.quit()
    print("disconnect ", sid)


if __name__ == "__main__":
    web.run_app(app, port=1337)
