import sys, re
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from api.config import get_mongo_connection  # Returns MongoDB collection

# def broward_recorder():
#     # Connect to MongoDB collection
#     mongo_collection = get_mongo_connection()

#     chrome_options = Options()
#     chrome_options.add_argument("--start-maximized")
#     driver = webdriver.Chrome(options=chrome_options)

#     try:
#         driver.get("https://officialrecords.broward.org/AcclaimWeb/")

#         # Click Document Type
#         WebDriverWait(driver, 15).until(
#             EC.element_to_be_clickable((By.ID, "mndoctype"))
#         ).click()
#         print("Clicked Document Type.")

#         # Accept terms if present
#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.ID, "btnButton"))
#             ).click()
#             print("Accepted terms.")
#         except TimeoutException:
#             print("No acceptance button found, continuing...")

#         # Open Document Type dropdown
#         WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "#DocTypesDisplay-input + span.t-select"))
#         ).click()
#         print("Opened Document Type dropdown.")

#         # Select DEED TRANSFERS OF REAL PROPERTY (D)
#         WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, "//li[contains(., 'DEED TRANSFERS OF REAL PROPERTY (D)')]"))
#         ).click()
#         print("Selected 'DEED TRANSFERS OF REAL PROPERTY (D)'.")

#         # Open Date Range dropdown
#         WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, "//span[@class='t-input' and text()='Specify Date Range...']/following-sibling::span"))
#         ).click()
#         print("Opened Date Range dropdown.")

#         # Select "Last Month"
#         WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, "//li[normalize-space()='Last Month']"))
#         ).click()
#         print("Selected 'Last Month'.")

#         # Click Search
#         WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.ID, "btnSearch"))
#         ).click()
#         print("Clicked Search.")

#         # Click push-pin toggle button to collapse/expand search form
#         try:
#             toggle_button = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.ID, "toggleForm"))
#             )
#             toggle_button.click()
#             print("Clicked push-pin toggle button.")
#         except TimeoutException:
#             print("Push-pin button not found, continuing...")

#         # Scroll to bottom to ensure all rows render
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(5)  # small wait for table to fully render

#         # Wait for table rows to appear
#         rows = WebDriverWait(driver, 30).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
#         )
#         print(f"Found {len(rows)} rows.")

#         inserted_count = 0
#         for row in rows:
#             cells = row.find_elements(By.TAG_NAME, "td")
#             if len(cells) < 2:
#                 continue

#             # Extract First Direct Name reliably
#             first_direct_name = driver.execute_script("return arguments[0].innerText;", cells[1]).strip()

#             if first_direct_name:
#                 mongo_collection.insert_one({"First Direct Name": first_direct_name})
#                 inserted_count += 1

#         print(f"Inserted {inserted_count} 'First Direct Name' records into MongoDB ({mongo_collection.full_name})")

#     finally:
#         driver.quit()

# Broward Appraiser Website
def broward_appraiser(job_name: str, search_value: str, website_type: str):
    # Connect to MongoDB collection
    mongo_collection = get_mongo_connection()

    # Create results folder based on job_name
    results_folder = f"C:/Users/USER/Documents/Python Scripts/smart_doc_intake/results/FL/Broward/Appraiser/{job_name}"
    os.makedirs(results_folder, exist_ok=True)
    print(f"Results will be saved in: {results_folder}")

    # Configure Chrome options for automatic PDF download
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    prefs = {
        "printing.print_preview_sticky_settings.appState": """{
            "recentDestinations": [{"id": "Save as PDF","origin": "local"}],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }""",
        "savefile.default_directory": results_folder
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--kiosk-printing")  # Auto print to PDF

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://web.bcpa.net/BcpaClient/#/Record-Search")

        # Wait for search input
        search_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "txtField"))
        )

        # Use the provided search_value
        search_input.clear()
        search_input.send_keys(search_value)

        # Click search button
        search_button = driver.find_element(By.ID, "searchButton")
        search_button.click()

        # Wait for results table to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table"))
        )
        time.sleep(3)
        print("Search completed and results loaded.")

        # Get folio number
        folio_element = driver.find_element(By.CSS_SELECTOR, "td.lblRecinfoDesc.searchTblCategory2 div#folioNumberId span a")
        folio_number = folio_element.text.strip()
        print(f"Folio number: {folio_number}")

        # Click the print button to generate PDF
        print_button = driver.find_element(By.CSS_SELECTOR, "div.btn-printrecinfo")
        print_button.click()
        time.sleep(5)  # Wait for PDF generation

        # Rename the most recent PDF to folio_number.pdf
        pdf_files = [f for f in os.listdir(results_folder) if f.lower().endswith(".pdf")]
        if pdf_files:
            latest_pdf = max([os.path.join(results_folder, f) for f in pdf_files], key=os.path.getctime)
            new_pdf_path = os.path.join(results_folder, f"{folio_number}.pdf")
            os.rename(latest_pdf, new_pdf_path)
            print(f"PDF renamed to: {new_pdf_path}")

        # Extract property details
        property_owners = driver.find_element(By.ID, "ownerNameId").text.strip()
        address = driver.find_element(By.ID, "situsAddressId").text.strip()
        year_built = driver.find_element(By.ID, "actualAgeId").text.strip()
        deputy_appraiser = driver.find_element(By.ID, "deputyAppraiserNameId").text.strip()
        property_appraiser_number = driver.find_element(By.ID, "phoneNumber").text.strip()
        try:
            property_image = driver.find_element(By.CSS_SELECTOR, "div#propertyImage img").get_attribute("src")
        except:
            property_image = None

        # Prepare MongoDB document
        doc = {
            "Job_Name": job_name,
            "Website_Type": website_type,   # NEW FIELD
            "Doc_Name": folio_number,
            "Property_Owners": property_owners,
            "Address": address,
            "Year_Built": year_built,
            "Deputy_Appraiser": deputy_appraiser,
            "Property_Appraiser_Number": property_appraiser_number,
            "Property_Image_Link": property_image,
            "PDF_Folder": results_folder
        }

        # ✅ Insert into MongoDB ONLY if everything succeeded
        mongo_collection.insert_one(doc)
        print("Data saved to MongoDB successfully.")

        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        driver.quit()

# Broward Revenue Collection Website
def broward_revenue(job_name: str, search_value: str, website_type: str):
    print("[START] broward_revenue")

    # Connect to MongoDB collection
    print("[INFO] Connecting to MongoDB...")
    mongo_collection = get_mongo_connection()

    # ---- Downloads folder ----
    results_folder = (
        f"C:/Users/USER/Documents/Python Scripts/smart_doc_intake/"
        f"results/FL/Broward/Revenue Collection/{job_name}"
    )
    os.makedirs(results_folder, exist_ok=True)
    print(f"[INFO] Results folder ready: {results_folder}")

    # ---- Chrome options (force PDF download) ----
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": results_folder.replace("/", "\\"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    })

    print("[INFO] Launching Chrome...")
    driver = webdriver.Chrome(options=chrome_options)

    def wait_for_new_pdf(before: set, timeout=90) -> str:
        print("[DEBUG] Waiting for new PDF...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            after = set(os.listdir(results_folder))
            diff = after - before
            if any(name.lower().endswith(".crdownload") for name in diff):
                time.sleep(0.5)
                continue
            pdfs = [name for name in diff if name.lower().endswith(".pdf")]
            if pdfs:
                pdfs.sort(key=lambda n: os.path.getmtime(os.path.join(results_folder, n)), reverse=True)
                found = os.path.join(results_folder, pdfs[0])
                print(f"[DEBUG] PDF detected: {found}")
                return found
            time.sleep(0.5)
        raise TimeoutError("PDF download timed out")

    try:
        print("[STEP 1] Navigating to site...")
        driver.get("https://county-taxes.net/broward/property-tax")

        # Close notification popup if present
        print("[STEP 2] Checking for popup...")
        try:
            close_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.close-button"))
            )
            close_btn.click()
            print("[INFO] Closed popup.")
        except Exception:
            print("[INFO] No popup found.")

        # Search
        print("[STEP 3] Searching folio/account...")
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[role='searchbox']"))
        )
        search_box.clear()
        search_box.send_keys(search_value)
        search_box.send_keys(Keys.RETURN)
        print(f"[INFO] Search submitted: {search_value}")

        # [STEP 4] Wait for iframe and switch
        try:
            iframe = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
            )
            driver.switch_to.frame(iframe)
            print("[INFO] Switched into results iframe.")
        except Exception as e:
            print(f"[ERROR] Could not switch to iframe: {e}")
            driver.quit()
            return

        # Rows
        print("[STEP 5] Waiting for bill rows...")
        rows = WebDriverWait(driver, 25).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.regular"))
        )
        print(f"[INFO] Found {len(rows)} bill rows.")

        # Only take top 3
        rows = rows[:3]
        print(f"[INFO] Processing {len(rows)} rows...")

        docs = []
        for i, row in enumerate(rows, start=1):
            print(f"[STEP 6] Processing row {i}...")

            desc_a = row.find_element(By.CSS_SELECTOR, "th.description a")
            desc_text = desc_a.text.strip()
            print(f"[DEBUG] Desc: {desc_text}")
            m = re.search(r"\b(20\d{2})\b", desc_text)
            tax_year = m.group(1) if m else desc_text

            amount_due_raw = row.find_element(By.CSS_SELECTOR, "td.balance").text.strip()
            amount_due = amount_due_raw.replace("$", "").strip()
            print(f"[DEBUG] Amount Due: {amount_due}")

            status_td = row.find_element(By.CSS_SELECTOR, "td.status")
            amount_paid = status_td.find_element(By.CSS_SELECTOR, "span[translate='no']").text.strip()
            print(f"[DEBUG] Amount Paid: {amount_paid}")

            payment_date = row.find_element(By.CSS_SELECTOR, "td.as-of time").text.strip()
            print(f"[DEBUG] Payment Date: {payment_date}")

            message_td = row.find_element(By.CSS_SELECTOR, "td.message")
            status_label = message_td.find_element(By.CSS_SELECTOR, "span.label").text.strip()
            receipt_no = message_td.find_element(By.CSS_SELECTOR, "span[translate='no']").text.strip()
            status_value = f"{status_label} {receipt_no}"
            print(f"[DEBUG] Status: {status_value}")

            # Download
            before_files = set(os.listdir(results_folder))
            print("[STEP 7] Clicking print link...")
            print_link = row.find_element(By.CSS_SELECTOR, "td.actions a[href*='/print']")
            driver.execute_script("arguments[0].click();", print_link)

            downloaded_path = wait_for_new_pdf(before_files, timeout=120)
            print(f"[INFO] Download complete: {downloaded_path}")

            new_name = f"{search_value}-{tax_year}-T{i}.pdf"
            final_path = os.path.join(results_folder, new_name)
            base, ext = os.path.splitext(final_path)
            suffix = 1
            while os.path.exists(final_path):
                final_path = f"{base}({suffix}){ext}"
                suffix += 1
            os.replace(downloaded_path, final_path)
            print(f"[INFO] File renamed to: {final_path}")

            docs.append({
                "Job_Name": job_name,
                "Website_Type": website_type,
                "Doc_Name": f"{search_value}-{tax_year}-T{i}",
                "Amount_Due": amount_due,
                "Amount_Paid": amount_paid,
                "Payment_Date": payment_date,
                "Status": status_value
            })

        if docs:
            mongo_collection.insert_many(docs)
            print(f"[INFO] Inserted {len(docs)} docs into MongoDB.")

        print("[SUCCESS] broward_revenue finished OK.")
        return True

    except Exception as e:
        print(f"[ERROR] broward_revenue crashed: {e}")
        return False

    finally:
        try:
            driver.quit()
            print("[INFO] Driver closed.")
        except Exception:
            pass
