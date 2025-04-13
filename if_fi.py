from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
import time
import os
import traceback
import requests
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from twocaptcha import TwoCaptcha
from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import RecaptchaV2ProxylessRequest
import asyncio
import re
from error_reporting import handle_scraper_error

os.environ["SE_CACHE_PATH"] = "/tmp/selenium_cache"
# 2Captcha API Key
API_KEY = "6eac18b9d70d016d0dcdaf58772e934b"

CAPMONSTER_API_KEY = "ec604c6ab64f34e3aba1b53684b5a706"

client_options = ClientOptions(api_key=CAPMONSTER_API_KEY)
cap_monster_client = CapMonsterClient(options=client_options)

# Site details
SITE_KEY = "6LeyeaIdAAAAAJ8dQECv_rT21tnllZ7iow927wYm"
PAGE_URL = "https://www.if.fi/henkiloasiakkaat/vakuutukset/autovakuutus"

USERNAME = "u07482d15574405cb-zone-custom-region-eu"
PASSWORD = "u07482d15574405cb"
PROXY_DNS = "118.193.58.115:2333"


def get_proxy():
    """
    Fetches a new proxy dynamically using provided credentials.
    Returns a dictionary containing HTTP and HTTPS proxy settings.
    """
    proxy_url = f"http://{USERNAME}:{PASSWORD}@{PROXY_DNS}"
    return {"http": proxy_url, "https": proxy_url}


def check_ip():
    """
    Checks and prints the current IP address to verify if the proxy is working.
    """
    print("Proxy test")
    proxy = get_proxy()
    try:
        response = requests.get("http://ip-api.com/json", proxies=proxy, timeout=10)
        ip_data = response.json()
        print(f"Current Proxy IP: {ip_data.get('query', 'Unknown')} ({ip_data.get('country', 'Unknown')})")
    except requests.exceptions.RequestException:
        print("Failed to fetch IP address. Proxy might be blocked!")


def solve_captcha_2captcha(driver, site_key, page_url):
    """
    Detects and solves a reCAPTCHA challenge using the 2Captcha API.
    Injects the solution into the page and submits the form.
    """
    print("Checking for reCAPTCHA...")
    try:
        recaptcha_iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
        )
        print("reCAPTCHA detected. Solving...")

        solver = TwoCaptcha(API_KEY)
        result = solver.recaptcha(sitekey=site_key, url=page_url)
        captcha_code = result['code']

        driver.execute_script(
            "document.getElementById('g-recaptcha-response').innerHTML = arguments[0];",
            captcha_code
        )
        print("CAPTCHA solved, injecting response.")

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]'))
        )
        submit_button.click()
        print("Form submitted successfully after solving CAPTCHA!")

    except:
        print("No reCAPTCHA found. Proceeding without solving.")


def solve_captcha_capmonster(driver, site_key, page_url, retries=3, wait_time=5):
    print("Checking for reCAPTCHA...")
    try:
        # Wait for the reCAPTCHA iframe and check if it exists
        try:
            recaptcha_iframe = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            if recaptcha_iframe:  # Only proceed if reCAPTCHA is found
                print("reCAPTCHA detected. Solving...")

                # Create CAPTCHA solving request
                recaptcha_request = RecaptchaV2ProxylessRequest(websiteUrl=page_url, websiteKey=site_key)

                # Run the async function properly
                result = asyncio.run(cap_monster_client.solve_captcha(recaptcha_request))
                captcha_code = result['gRecaptchaResponse']
                # print(f"CAPTCHA solved: {captcha_code}")

                # Inject the CAPTCHA response into the form
                driver.execute_script(
                    "document.getElementById('g-recaptcha-response').innerHTML = arguments[0];",
                    captcha_code
                )
                print("CAPTCHA solved, injecting response.")

                submit_button = WebDriverWait(driver, wait_time).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]'))
                )
                submit_button.click()
                print("Form submitted successfully after solving CAPTCHA!")
                return True
        except Exception as e:
            print("No CAPTCHA found, proceeding without solving.")
            return True  # If no CAPTCHA is found, return True since we don't need to solve it.

    except Exception as e:
        print(f"Error occurred while solving CAPTCHA: {e}")
        return False


def if_fi_scraping(headless_scrapper, pause_scrapper_at_the_end, requestID, annual_mileage, financed, financing_company,
                   insurance_start_date, municipality, personal_id, postal_code, registration_number, under_24):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")  # Fix root user issues
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues
    # chrome_options.add_argument("--user-data-dir=/tmp/chrome_user_data")  # Unique user data directory
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
    chrome_options.add_argument(
        f"--proxy-pac-url=data:text/javascript,{{'FindProxyForURL': function(url, host) {{ return 'PROXY {PROXY_DNS}'; }}}}")
    chrome_options.add_argument("start-maximized")

    if headless_scrapper == "true":
        # chrome_options.add_argument("--headless")  # Run without GUI
        chrome_options.add_argument("--headless=new")
    else:
        chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("--auto-open-devtools-for-tabs")  # Opens DevTools automatically

    check_ip()
    driver = webdriver.Chrome(options=chrome_options)

    timing_log = {}

    try:
        start_time = time.time()
        driver.get("https://www.if.fi/henkiloasiakkaat/vakuutukset/autovakuutus")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#qst_11631_24c590b5-a868-4504-9612-6aaa08f75aa2")))

        timing_log["page_load"] = time.time() - start_time

        start_time = time.time()

        # Check if the element exists before clicking
        elements = driver.find_elements(By.CSS_SELECTOR, '#onetrust-accept-btn-handler')
        if elements:
            elements[0].click()
            # print("Cookie consent button clicked.")
        # else:
        # print("Cookie consent button not found, skipping.")

        driver.find_element(By.CSS_SELECTOR, '#qst_11631_24c590b5-a868-4504-9612-6aaa08f75aa2').send_keys(
            registration_number)
        driver.find_element(By.CSS_SELECTOR, '#qst_11630_9941162d-0136-4489-b0ab-adecca269141').send_keys(personal_id)
        timing_log["registration_number_personal_id"] = time.time() - start_time

        start_time = time.time()
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "entryFormSubmit"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(1)
        ActionChains(driver).move_to_element(element).click().perform()
        timing_log["submit"] = time.time() - start_time

        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".DependentTrigger_19838"))
            )
        except TimeoutException:
            print("Element not clickable within 10 seconds, solving CAPTCHA...")
            driver.save_screenshot("1before_captcha_solve.png")

            # Call CAPTCHA-solving function here
            solve_captcha_capmonster(driver, SITE_KEY, PAGE_URL)
            driver.save_screenshot("after_captcha_solve.png")
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".DependentTrigger_19838"))
            )

        # Odabir finansiranja
        # if financed == 'no':
        #     driver.find_element(By.CSS_SELECTOR, '.DependentTrigger_19838').click()
        # else:
        #     driver.find_element(By.CSS_SELECTOR, '.DependentTrigger_19837').click()

        # Odabir godine starosti vozaca
        if under_24 == 'no':
            driver.find_element(By.CSS_SELECTOR,
                                '#ctl07_ucProcess_ucTopQuestions_qst_15383 > span.webshop-dependent-trigger.DependentTrigger_15389.ecmt-form-item-label-is-radio').click()
        else:
            driver.find_element(By.CSS_SELECTOR,
                                '#ctl07_ucProcess_ucTopQuestions_qst_15383 > span.webshop-dependent-trigger.DependentTrigger_15388.ecmt-form-item-label-is-radio').click()

        if (annual_mileage == "50000+"):
            annual_mileage = "51000"

        # Odabir kilometraže

        select_element = Select(driver.find_element(By.ID, "ctl07_ucProcess_ucTopQuestions_qst_15370"))
        select_element.select_by_value("5000")  # Replace with the actual value

        # # Select by value
        # select_element.select_by_value("5000")  # Replace with the actual value
        # driver.find_element(By.CSS_SELECTOR,"#ctl07_ucProcess_ucTopQuestions_qst_15370 .select2-selection__rendered").click()
        # time.sleep(500)
        # driver.find_element(By.CSS_SELECTOR,".select2-results__options li:nth-child(1)").click()

        driver.find_element(By.CSS_SELECTOR, '#ctl07_ucProcess_ucTopQuestions_qst_11655').send_keys(
            insurance_start_date)

        driver.find_element(By.CSS_SELECTOR, '#ctl07_ucProcess_ucTopQuestions_qst_12535').send_keys(
            "En halua antaa osoitetietojani")

        driver.find_element(By.CSS_SELECTOR, '#ctl07_ucProcess_ucTopQuestions_qst_11634').send_keys(postal_code)
        timing_log["second_page_details_entry"] = time.time() - start_time

        # final submit
        start_time = time.time()
        driver.find_element(By.CSS_SELECTOR, '#ctl07_ucProcess_ucTopQuestions_btnMiddleStepPrice').click()
        timing_log["final_submit"] = time.time() - start_time

        # Wait for the comparison table to load
        start_time = time.time()
        comparison_table = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'packageheaderid'))
        )
        timing_log["final_load_complete"] = time.time() - start_time
        start_time = time.time()
        counter = -1
        allData = []

        bonuses_found = driver.find_elements(By.CSS_SELECTOR, '[class^="MotorBonusBanner__bonusBox"]')
        bonusesA = {}
        if bonuses_found:
            bonusesA["motor_insurance_bonus"] = bonuses_found[0].find_element(By.CSS_SELECTOR,
                                                                              '[class^="MotorBonusBanner__bonusBoxBonus"]').text
            bonusesA["comprehensive_insurance_bonus"] = bonuses_found[1].find_element(By.CSS_SELECTOR,
                                                                                      '[class^="MotorBonusBanner__bonusBoxBonus"]').text

        package_general = driver.find_elements(By.CSS_SELECTOR,
                                               ".PackageHeaderRows__packageHeaderFirstRow___2vlD8 .PackageHeaderBox__packageHeaderBox___LmREQ")
        for package in package_general:
            package_title = package.find_element(By.CSS_SELECTOR, ".title")
            package_title.click()
            package_name = package_title.text
            package_price = package.find_element(By.CSS_SELECTOR, ".PackagePrice__priceContainer___2w4R8  ").text

            deductibles_found = driver.find_elements(By.CSS_SELECTOR, '[class*="DeductiblesButton"]')
            deductibles = []
            if deductibles_found:
                for deductible in deductibles_found:
                    deductibles.append(deductible.text)
            allData.append({
                "insurer_name": "if.fi",
                "offer_name": package_name,
                "offer_price": re.sub(r'\s*€.*', '', package_price),
                "additional_coverages_included": [],
                "additional_coverages_buyable": [],
                "bonuses": bonusesA,
                "deductibles": deductibles
            })

            # additional_buyables = driver.find_elements(By.CSS_SELECTOR, ".Matrix__matrixCheckRow___2hH7Z")

        package_details = driver.find_elements(By.CSS_SELECTOR,
                                               ".Matrix__comparisonMatrix___3LceP>div:last-child>div:first-child .Matrix__matrixCheckRow___2hH7Z")
        additional_coverages_names = []
        for row in package_details:
            option_name = row.find_element(By.CSS_SELECTOR, ".Matrix__title___jvIAk").text
            additional_coverages_names.append(option_name)
            cells = row.find_elements(By.CSS_SELECTOR, ".Matrix__matrixCell___1Q5C5")
            counter = -1
            for cell in cells:
                counter += 1
                driver.implicitly_wait(0)  # Set implicit wait to 0 seconds
                # positive_elements = cell.find_elements(By.CSS_SELECTOR, ".Matrix__checked___2U5WW ")
                class_attribute = cell.get_attribute('class')
                if 'Matrix__checked___2U5WW' in class_attribute.split():
                    # print(f"{option_name}-included")
                    allData[counter]["additional_coverages_included"].append({
                        "name": option_name,
                        "included": "true"
                    })
                    # else:
                #     print(f"{option_name}-notincluded")
                #     allData[counter]["additional_coverages_included"].append({
                #         "name" : option_name,
                #         "included" : "false"
                #     })

        package_details = driver.find_elements(By.CSS_SELECTOR,
                                               ".Matrix__comparisonMatrix___3LceP>div:last-child>div:last-child .Matrix__matrixCheckRow___2hH7Z")
        for row in package_details:
            option_name = row.find_element(By.CSS_SELECTOR, ".Matrix__title___jvIAk span").text
            option_price = row.find_element(By.CSS_SELECTOR,
                                            ".Matrix__title___jvIAk .Matrix__addonYearlyPrice___1LNrL").text
            additional_coverages_names.append(option_name)
            cells = row.find_elements(By.CSS_SELECTOR, ".Matrix__matrixCell___1Q5C5")
            counter = -1
            for cell in cells:
                counter += 1
                driver.implicitly_wait(0)  # Set implicit wait to 0 seconds
                buyable_element = cell.find_elements(By.CSS_SELECTOR, ".AddonCheckbox__btxFormCheckbox___1asKb")
                if buyable_element:
                    allData[counter]["additional_coverages_buyable"].append({
                        "name": option_name,
                        "price": option_price
                    })

        timing_log["final_processing_complete"] = time.time() - start_time

        response = {
            'status': 200,
            'data': {
                "offers": allData,
                "bonuses": bonusesA
            },
            'timings': timing_log
        }
        if pause_scrapper_at_the_end == "true":
            print(response)
            time.sleep(100000)
        return response





    except Exception as e:
        return handle_scraper_error(driver, requestID, pause_scrapper_at_the_end)
        error_details = traceback.format_exc()
        # print(f"An error occurred!!: {str(e)}|{error_details}")

        error_details = traceback.format_exc()

        WEBHOOK_URL = "https://discord.com/api/webhooks/1350966090301308978/FFoPYWj6aXxinO30c9zrfURmDadOLlQ8YpYw815YCcWiQzL3gw-FMAloxtylp-TeDhxU"
        payload = {"content": error_details}
        response = requests.post(WEBHOOK_URL, payload)
        print("discord response", response)

        error_dir = f"logs/errors/{time.strftime('%Y-%m-%d')}"
        os.makedirs(error_dir, exist_ok=True)  # Ensure the directory exists

        request_name = f"{time.strftime('%Y%m%d-%H-%M-%S')}-{requestID}"
        error_file_path = f"{error_dir}/{request_name}"

        with open(f"{error_file_path}.txt", "w", encoding="utf-8") as file:
            file.write(traceback.format_exc())

        full_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        full_height = driver.execute_script('return document.body.parentNode.scrollHeight') + 150
        driver.set_window_size(full_width, full_height)
        driver.save_screenshot(f"{error_file_path}.png")

        if pause_scrapper_at_the_end == "true":
            print(response)
            time.sleep(100000)

        error_response = {
            'status': 500,
            'data': {
                "error": error_details,
                "error_file_path": error_file_path
            }
        }
        # WEBHOOK_URL = "https://discord.com/api/webhooks/1350966090301308978/FFoPYWj6aXxinO30c9zrfURmDadOLlQ8YpYw815YCcWiQzL3gw-FMAloxtylp-TeDhxU"
        # response = requests.post(WEBHOOK_URL, json=error_response)

        return error_response

    finally:
        driver.quit()

if_fi_scraping(True,False,"whatever","5000","yes","","2024-02-01","","200992-248W","00100","LSO-589","true")
