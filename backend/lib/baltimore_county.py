from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import urllib.parse
import urllib.request
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdb
import asyncio
from logger import log
from driver import release_driver, get_driver


async def fetchAccountNumber(address):
    log("debug", f"Fetching account number for address {address}")
    # Set the URL and request body
    url = "https://pay.baltimorecity.gov/water/_getInfoByServiceAddress"
    data = urllib.parse.urlencode({"serviceAddress": address}).encode("utf-8")

    # Set the headers
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Create the request
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    # Perform the request and read the response
    with urllib.request.urlopen(req) as response:
        response_text = response.read().decode("utf-8")
        return response_text


async def pickAccountNumber(address):
    log("debug", f"Picking account number for address {address}")
    account_number_response_html = await fetchAccountNumber(address)
    root = BeautifulSoup(account_number_response_html, "html.parser")
    table = root.table
    rows = table.find_all("tr")
    # ignore all the rows that don't have a td
    rows = [row for row in rows if row.find("td")]
    if len(rows) > 1:
        pdb.set_trace()
        print("There are multiple accounts for address " + address)
        print("Which would you like to use?")
        for i, row in enumerate(rows):
            print(f"{i}: {row.find('td').text}")
        choice = int(input("Enter the number of the account you want to use: "))
        accountNumber = rows[choice].find("td").text
        print(f"Using account number {accountNumber}")
        return accountNumber
    else:
        accountNumber = rows[0].find("td").text
        log("success", f"Found account number {accountNumber}")
        log("success", f"Using Account number: {accountNumber}")
        return accountNumber


async def baltimore_find_account_id_and_scrape(address, driver):
    log("debug", f"Beginning scraping for {address}")
    while driver is None:
        driver = await get_driver()

    try:
        account_number = await pickAccountNumber(address)
        driver.get("https://pay.baltimorecity.gov/water")
        script = f'document.getElementById("accountNumber").value = "{account_number}";'
        driver.execute_script(script)
        enableButtonManually = (
            f'document.getElementById("buttonSubmitAccountNumber").disabled = false;'
        )
        driver.execute_script(enableButtonManually)
        driver.execute_script(
            f'document.getElementById("buttonSubmitAccountNumber").click();'
        )

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
        )
        root = BeautifulSoup(driver.page_source, "html.parser")
        table = root.find("table", {"class": "table-striped"})
        rows = table.find_all("tr")
        rows = [row for row in rows if row.find("td")]
        data = {}
        for row in rows:
            key = row.find("td")
            if (
                key.has_attr("colspan")
                or key.text.strip() is None
                or key.text.strip() == ""
                or len(key.find_all("span")) > 0
                or len(key.find_all("strong")) > 0
                or len(key.find_all("div")) > 0
            ):
                continue

            key = row.find_all("td")
            if len(key) == 2:
                data[key[0].text.strip()] = key[1].text.strip()
            data[key[0].text.strip()] = key[1].text.strip()
        log("success", f"Finished scraping for {address}")
        await release_driver(driver)
        log("success", f"Scraped Data:  {data}")
        return data
    except Exception as e:
        log("error", f"Error scraping baltimore county: {e}")
        import traceback

        traceback.print_exc()
        return None
