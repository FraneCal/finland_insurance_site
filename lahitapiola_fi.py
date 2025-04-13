import time
import os
import traceback
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import re
from error_reporting import handle_scraper_error

os.environ["SE_CACHE_PATH"] = "/tmp/selenium_cache"


def lahitapiola(headless_scrapper, pause_scrapper_at_the_end, requestID, annual_mileage, financed, financing_company,
                insurance_start_date, municipality, personal_id, postal_code, registration_number, under_24):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")  # Fix root user issues
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues
    # chrome_options.add_argument("--user-data-dir=/tmp/chrome_user_data")  # Unique user data directory
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
    chrome_options.add_argument("--incognito")
    if headless_scrapper == "true":
    # chrome_options.add_argument("--headless=new")
        pass
    else:
        chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("--auto-open-devtools-for-tabs")  # Opens DevTools automatically
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://verkkopalvelu.lahitapiola.fi/e2/autovakuutus/vakuutuslaskuri/")
        driver.implicitly_wait(10)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#onetrust-accept-btn-handler")))
        driver.find_element(By.CSS_SELECTOR, '#onetrust-accept-btn-handler').click()

        # driver.execute_script("document.getElementsByName('postalCode')[0].value = arguments[0];", postal_code)

        # driver.execute_script("document.getElementsByName('ssn')[0].value = arguments[0];", personal_id)
        # driver.find_element(By.NAME, 'postalCode').click()

        registration = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "choose-vehicle-reg-number"))
        )
        registration.click()
        driver.execute_script("arguments[0].value = arguments[1];", registration, registration_number)

        # postal_code_input = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.CSS_SELECTOR, "#choose-vehicle-reg-number"))
        # )
        # postal_code_input.click()
        # driver.execute_script("arguments[0].value = arguments[1];", postal_code_input, postal_code)

        ssn_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#choose-vehicle-ssn"))
        )
        ssn_input.click()
        driver.execute_script("arguments[0].value = arguments[1];", ssn_input, personal_id)

        # Wait until the shadow host is present
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#choose-vehicle-search-button'))
        )
        # Access the shadow root
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        # Try to find the button inside the shadow DOM
        button_inside_shadow = shadow_root.find_element(By.CSS_SELECTOR,
                                                        'button.duet-button.duet-button-size-medium.primary.medium')
        # Print outer HTML to verify it's the right element
        print(driver.execute_script("return arguments[0].outerHTML;", button_inside_shadow))
        # Or print its text (if there is any visible text)
        print("Button text:", button_inside_shadow.text)

        button_inside_shadow.click()
        time.sleep(10000)

        driver.find_element(By.CSS_SELECTOR,
                            '#DuetChoice-d72800e8-1ba8-4928-40e8-698a08de6434').click()  # private use yes
        time.sleep(10000)

        driver.implicitly_wait(5)

        radio_button = driver.find_elements(By.CLASS_NAME, 'duet-checkmark-radio')
        radio_button[1].click()
        shadow_host1 = driver.find_element(By.CSS_SELECTOR, '#vehicleInfoForm0 > duet-grid > duet-button')
        shadow_root1 = driver.execute_script("return arguments[0].shadowRoot", shadow_host1)
        dugme1 = shadow_root1.find_element(By.CSS_SELECTOR, 'button')
        dugme1.click()

        shadow_host2 = driver.find_element(By.CSS_SELECTOR,
                                           '#checkVehicleInformationForm0 > duet-grid > duet-button.next.hydrated')
        shadow_root2 = driver.execute_script("return arguments[0].shadowRoot", shadow_host2)
        shadow_host2.click()

        allData = []

        packages = driver.find_elements(By.CSS_SELECTOR, "#content duet-step:nth-child(4) .itemWrapper")
        for item in packages:
            package_name = item.find_element(By.CSS_SELECTOR, "label")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", package_name)
            # print("package",package_name.text)

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(package_name)).click()
            price = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".duet-font-size-large.duet-font-weight-extra-bold")))
            # print("price", price.text)

            deductiblesA = []
            deductibles = driver.find_elements(By.CSS_SELECTOR,
                                               'duet-choice-group[name="deductible"] [name="deductible"]+label')
            if deductibles:
                for deductible in deductibles:
                    print("deductible found!!!")
                    deductiblesA.append(deductible.text)

            additional_coverages_included = []
            rows = driver.find_elements(By.CSS_SELECTOR, ".duet-responsive-table tbody tr")
            if (rows):
                for row in rows:
                    item_name = row.find_element(By.CSS_SELECTOR, "td:first-child")
                    # print(item_name.text)
                    if (row.find_elements(By.CSS_SELECTOR, "duet-icon")):
                        additional_coverages_included.append({
                            "name": item_name.text,
                            "included": "true"
                        })

            driver.find_element(By.CSS_SELECTOR,
                                ".is-current duet-button.next").click()  # go to next step to fetch bonuses
            driver.implicitly_wait(0)  # Set implicit wait to 0 seconds
            bonuses_found = driver.find_elements(By.CSS_SELECTOR, '.is-current duet-list')
            bonuses = {}
            if bonuses_found:
                for bonus in bonuses_found:
                    if (bonus.find_element(By.CSS_SELECTOR, '[slot="label"]').text == "Liikennevakuutuksen bonus"):
                        bonuses["motor_insurance_bonus"] = bonus.find_element(By.CSS_SELECTOR, '[slot="value"]').text
                    else:
                        bonuses["comprehensive_insurance_bonus"] = bonus.find_element(By.CSS_SELECTOR,
                                                                                      '[slot="value"]').text

            previous_step = driver.find_element(By.CSS_SELECTOR,
                                                '[heading="Valitse vakuutusturvan laajuus"]')  # go to next step to fetch bonuses
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", previous_step)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(previous_step)).click()

            allData.append({
                "insurer_name": "lahitapiola.fi",
                "offer_name": package_name.text,
                "offer_price": re.sub(r'\s*€.*', '', price.text),
                "additional_coverages_included": additional_coverages_included,
                "additional_coverages_buyable": [],
                "bonuses": bonuses,
                "deductibles": deductiblesA
            })

        response = {
            'status': 200,
            'data': {
                "offers": allData,
            },
            'timings': ""
        }
        if pause_scrapper_at_the_end == "true":
            print(response)
            time.sleep(100000)
        return response



    except Exception as e:
        print(f"Lahtipiola.fi an error occurred: {str(e)}")
        return handle_scraper_error(driver, requestID, pause_scrapper_at_the_end)

        print(f"Lahtipiola.fi an error occurred: {str(e)}")
        error_details = traceback.format_exc()

        error_dir = f"logs/errors/{time.strftime('%Y-%m-%d')}"
        os.makedirs(error_dir, exist_ok=True)  # Ensure the directory exists

        request_name = f"{time.strftime('%Y%m%d-%H-%M-%S')}-{requestID}"
        error_file_path = f"{error_dir}/{request_name}"

        full_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        full_height = driver.execute_script('return document.body.parentNode.scrollHeight') + 150
        driver.set_window_size(full_width, full_height)
        driver.save_screenshot(f"{error_file_path}.png")

        with open(f"{error_file_path}.txt", "w", encoding="utf-8") as file:
            file.write(traceback.format_exc())

        return {
            'status': 500,
            'data': {
                "error": error_details,
                "error_file_path": error_file_path
            }
        }
    finally:
        driver.quit()

result = lahitapiola(
    headless_scrapper=["headless_scrapper"],
    pause_scrapper_at_the_end=["scraper_pause_at_the_end"],
    requestID=["requestID"],
    annual_mileage=["annual_mileage"],
    financed=["financed"],
    financing_company=["financing_company"],
    insurance_start_date=["insurance_start_date"],
    municipality=["municipality"],
    personal_id=["personal_id"],
    postal_code=["postal_code"],
    registration_number=["registration_number"],
    under_24=["under_24"]
)
