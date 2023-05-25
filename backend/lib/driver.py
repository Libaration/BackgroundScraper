from logger import log
import threading
import baltimore_county as scraper
import asyncio

# Initialize driver-related variables
available_drivers = []
driver_lock = threading.Lock()


def get_driver():
    log("debug", "Checking for available drivers...")
    log("debug", f"Number of available drivers: {len(available_drivers)}")
    log("debug", f"Available drivers: {available_drivers}")
    """Get an available driver or create a new one if none are available."""
    with driver_lock:
        if available_drivers:
            log("debug", "Reusing driver")
            return available_drivers.pop()
        else:
            log("debug", "Creating new driver")
            driver = scraper.start_driver()
            log("success", f"New driver created: {driver}")
            return driver


def release_driver(driver):
    """Release the driver and make it available for reuse."""
    available_drivers.append(driver)
    log("debug", f"Driver released: {driver}")


async def create_driver():
    """Create a new driver in an asynchronous thread."""
    return await asyncio.to_thread(scraper.start_driver)
