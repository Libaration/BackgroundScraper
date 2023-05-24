from time import sleep
from selenium import webdriver
import chromedriver_autoinstaller as chromedriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import urllib.parse
import urllib.request
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pdb


def start_driver():
    chromedriver.install()
    options = Options()
    options.page_load_strategy = "none"
    options.add_argument("--headless")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error starting WebDriver: {e}")
        driver = None
    return driver


def fetchAccountNumber(address):
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


def pickAccountNumber(address):
    root = BeautifulSoup(fetchAccountNumber(address), "html.parser")
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
        print("Found one account for address " + address)
        print(f"Using account number {accountNumber}")
        return accountNumber


def scrape_baltimore_county(address, driver):
    try:
        account_number = pickAccountNumber(address)
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

        WebDriverWait(driver, 10).until(
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
        print("Retrieved data for address " + address)
        return data
    except Exception as e:
        print(f"Error scraping baltimore county: {e}")
        return None
