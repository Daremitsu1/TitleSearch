from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def open_broward_site():
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    # Initialize Chrome (no driver path needed in Selenium 4.6+)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://officialrecords.broward.org/AcclaimWeb/")
        time.sleep(10)  # wait 10 seconds
    finally:
        driver.quit()

if __name__ == "__main__":
    open_broward_site()
