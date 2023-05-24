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


def start_driver():
    chromedriver.install()
    options = Options()
    options.page_load_strategy = "none"
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
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
    driver.get("https://pay.baltimorecity.gov/water")
    account_number = pickAccountNumber(address)
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
    # example driver.page_source
    # # <table class="table table-hover table-striped">
    #                                     <tbody>
    #                                         <tr><td colspan="2"><strong>Account Identification</strong></td></tr>
    #                                         <tr><td>Account Number</td><td><span>11000338071</span></td></tr>
    #                                         <tr><td>Service Address</td><td>920 S CONKLING ST        </td></tr>
    #                                         <tr><td colspan="2"><strong>Current Billing Information</strong></td></tr>
    #                                             <tr><td>Current Read Date</td><td>04/22/2023</td></tr>

    #                                             <tr><td>Current Bill Date</td><td>05/03/2023</td></tr>

    #                                             <tr><td>Penalty Date</td><td>05/23/2023</td></tr>
    #                                         <tr><td>Current Bill Amount</td><td>$0.00</td></tr>
    #                                         <tr><td>Previous Balance</td><td>$0.00</td></tr>
    #                                         <tr><td>Current Balance</td><td>$0.00</td></tr>
    #                                         <tr><td colspan="2"><strong>Previous Billing Information</strong></td></tr>
    #                                             <tr><td>Previous Read Date</td><td>03/22/2023</td></tr>

    #                                         <tr><td colspan="2"><strong>Payment History</strong></td></tr>
    #                                             <tr><td>Last Pay Date</td><td>05/10/2023</td></tr>
    #                                         <tr><td>Last Pay Amount</td><td>$-69.72</td></tr>
    #                                         <tr><td colspan="2"><strong>Customer Information</strong></td></tr>
    #                                         <tr><td colspan="2">As a new initiative to communicate better with our customers, we are requiring citizens to submit their Email ID and Phone Number when paying their bills.</td></tr>
    #                                         <tr>
    #                                             <td>
    root = BeautifulSoup(driver.page_source, "html.parser")
    table = root.find("table", {"class": "table-striped"})
    rows = table.find_all("tr")
    rows = [row for row in rows if row.find("td")]
    data = {}
    for row in rows:
        # find_all td in row whos does not have a colspan example <tr><td colspan="2"><strong>Account Identification</strong></td></tr>
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
        data[key[0].text.strip()] = key[1].text.strip()
    return data
