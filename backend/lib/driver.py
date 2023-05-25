import asyncio
import concurrent.futures
from logger import log
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from socket_server import io
import chromedriver_autoinstaller as chromedriver
from tornado import queues, gen

# Initialize driver-related variables
total_drivers = []
MAX_DRIVERS = 10
driver_queue = queues.Queue(maxsize=MAX_DRIVERS)
driver_semaphore = asyncio.Semaphore(MAX_DRIVERS)

driver_queue_lock = asyncio.Lock()


def clear_driver_queue():
    """Clear the driver queue."""
    while not driver_queue.empty():
        driver_queue.get_nowait()


async def start_driver():
    """Start a driver and add it to the pool."""
    for i in range(2):
        create_driver_sync()


async def get_driver():
    """Get a driver from the pool or create a new one if the pool is empty."""
    while True:
        log("debug", f"Driver queue size: {driver_queue.qsize()}")
        log("debug", f"Total drivers: {len(total_drivers)}")

        try:
            driver = driver_queue.get_nowait()  # Await availability of a driver
            log("success", "Reusing driver")
            return driver
        except queues.QueueEmpty:
            if len(total_drivers) < MAX_DRIVERS:
                return await create_driver()
            else:
                await asyncio.sleep(1)  # Wait for a driver to become available


async def release_driver(driver):
    """Release the driver and make it available for reuse."""
    async with driver_queue_lock:
        driver_queue.put(driver)
        log("debug", f"Driver released: {driver}")


async def create_driver():
    """Create a new driver in a separate thread."""
    if len(total_drivers) < MAX_DRIVERS:
        # loop = asyncio.get_event_loop()
        driver = create_driver_sync()
        log("success", f"Driver started: {driver}")

        await io.emit("driver_count", len(total_drivers))
        return driver
    else:
        log("debug", "No available drivers")
        while True:
            try:
                driver = await driver_queue.get()  # Await availability of a driver
                log("success", "Reusing driver")
                return driver
            except queues.QueueEmpty:
                await asyncio.sleep(1)  # Wait for a driver to become available


def create_driver_sync():
    """Synchronous function to create a new driver."""
    chromedriver.install()
    options = Options()
    options.page_load_strategy = "none"
    options.experimental_options["prefs"] = {
        "profile.managed_default_content_settings.images": 2
    }
    options.experimental_options["prefs"] = {
        "profile.managed_default_content_settings.javascript": 2
    }
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    total_drivers.append(driver)
    driver_queue.put(driver)
    return driver
