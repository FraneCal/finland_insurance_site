import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import RecaptchaV2ProxylessRequest
from bs4 import BeautifulSoup

# CapMonster API Key
API_KEY = "YOUR API KEY"
WEBSITE_URL = "https://www.if.fi/henkiloasiakkaat/vakuutukset/autovakuutus"
WEBSITE_KEY = "6LeyeaIdAAAAAJ8dQECv_rT21tnllZ7iow927wYm"

client_options = ClientOptions(api_key=API_KEY)
cap_monster_client = CapMonsterClient(options=client_options)


def solve_captcha(driver, site_key, page_url, retries=3, wait_time=10):
    print("Checking for reCAPTCHA...")
    try:
        recaptcha_iframe = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
        )
        print("reCAPTCHA detected. Solving...")

        # Synchronously solve the CAPTCHA
        recaptcha_request = RecaptchaV2ProxylessRequest(websiteUrl=page_url, websiteKey=site_key)
        result = cap_monster_client.solve_captcha(recaptcha_request)
        captcha_code = result['gRecaptchaResponse']
        print(f"CAPTCHA solved: {captcha_code}")

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
        print(f"Error occurred while solving CAPTCHA: {e}")
        return False


def setup_driver():
    print("Setting up the WebDriver...")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    print("WebDriver initialized.")
    return driver


def fill_form(driver):
    print("Navigating to the form page...")
    driver.get(PAGE_URL)

    try:
        print("Checking for cookie popup...")
        accept_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
        )
        accept_cookies.click()
        print("Cookies accepted.")
    except:
        print("No cookies popup found.")

    print("Filling in the form...")
    input_field_1 = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11631_24c590b5-a868-4504-9612-6aaa08f75aa2"]'))
    )
    input_field_1.send_keys("LSO-589")
    print("First input field filled.")

    input_field_2 = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11630_9941162d-0136-4489-b0ab-adecca269141"]'))
    )
    input_field_2.send_keys("200992-248W")
    print("Second input field filled.")

    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]'))
    )
    submit_button.click()
    print("Form submitted.")
    time.sleep(5)


def select_dropdown_option(driver, dropdown_id, option_text):
    """Opens a Select2 dropdown and selects an option based on visible text."""
    print(f"Selecting option '{option_text}' from dropdown '{dropdown_id}'...")
    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f'//span[@aria-labelledby="select2-{dropdown_id}-container"]'))
    )
    dropdown.click()
    time.sleep(1)

    option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f'//li[contains(text(), "{option_text}")]'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", option)
    option.click()
    print(f"Option '{option_text}' selected.")


def second_form(driver):
    print("Filling the second form...")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_19836"]/span[2]/label'))
    ).click()
    print("First radio button selected.")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_15383"]/span[2]/label'))
    ).click()
    print("Second radio button selected.")

    select_dropdown_option(driver, "ctl07_ucProcess_ucTopQuestions_qst_15370", "10 000 km")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_12535"]'))
    ).send_keys("Kalastajatorpantie 1")
    print("Address entered.")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_11634"]'))
    ).send_keys("00330")
    print("Postal code entered.")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_btnMiddleStepPrice"]'))
    ).click()
    print("Second form submitted.")

    print("Extracting result details...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'MotorBonusBanner__bonusBox___1GCtJ'))
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    details = soup.find("div", class_="MotorBonusBanner__bonusBox___1GCtJ")

    print(details.getText() if details else "Details not found.")


def main():
    print("Starting the automation process...")
    driver = setup_driver()

    try:
        fill_form(driver)
        if solve_captcha(driver, WEBSITE_KEY, WEBSITE_URL):
            print("Moving to the second form...")
            second_form(driver)
            print("Process completed successfully!")
        else:
            print("CAPTCHA solving failed, stopping the process.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Closing the WebDriver...")
        time.sleep(10)
        driver.quit()
        print("WebDriver closed.")


if __name__ == "__main__":
    main()
