import sys
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from twocaptcha import TwoCaptcha
from bs4 import BeautifulSoup

# 2Captcha API Key
API_KEY = "YOUR API KEY"

# Site details
SITE_KEY = "6LeyeaIdAAAAAJ8dQECv_rT21tnllZ7iow927wYm"
PAGE_URL = "https://www.if.fi/henkiloasiakkaat/vakuutukset/autovakuutus"


def setup_driver():
    """Initialize and configure the Selenium WebDriver."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver


def solve_captcha(driver, site_key, page_url):
    """Solve reCAPTCHA if present."""
    try:
        # Check if CAPTCHA iframe exists
        recaptcha_iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
        )
        print("reCAPTCHA detected. Solving...")

        # Solve CAPTCHA using 2Captcha
        solver = TwoCaptcha(API_KEY)
        result = solver.recaptcha(sitekey=site_key, url=page_url)
        captcha_code = result['code']

        # Inject CAPTCHA solution
        driver.execute_script(
            "document.getElementById('g-recaptcha-response').innerHTML = arguments[0];",
            captcha_code
        )

        # Click submit button again
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]'))
        )
        submit_button.click()

        print("Form submitted successfully after solving CAPTCHA!")

    except:
        print("No reCAPTCHA found. Proceeding without solving.")


def fill_form(driver):
    """Automate form filling and submission."""
    driver.get(PAGE_URL)

    # Accept cookies
    try:
        accept_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
        )
        accept_cookies.click()
    except:
        print("No cookies popup found.")

    # Fill in input fields
    input_field_1 = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11631_24c590b5-a868-4504-9612-6aaa08f75aa2"]'))
    )
    input_field_1.send_keys("LSO-589")

    input_field_2 = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11630_9941162d-0136-4489-b0ab-adecca269141"]'))
    )
    input_field_2.send_keys("200992-248W")

    # Click submit
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]'))
    )
    submit_button.click()

    # Wait a few seconds for reCAPTCHA to possibly appear
    time.sleep(5)


def select_dropdown_option(driver, dropdown_id, option_text):
    """Opens a Select2 dropdown and selects an option based on visible text."""

    # Click on the visible dropdown to open it
    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f'//span[@aria-labelledby="select2-{dropdown_id}-container"]'))
    )
    dropdown.click()
    time.sleep(1)  # Wait briefly for options to load

    # Find and click the option using its text
    option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f'//li[contains(text(), "{option_text}")]'))
    )

    # Scroll into view (sometimes necessary)
    driver.execute_script("arguments[0].scrollIntoView(true);", option)

    # Click the option
    option.click()


def second_form(driver):
    """Fills the second form with dropdown selections and text inputs."""

    # Click radio buttons
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_19836"]/span[2]/label'))
    ).click()

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_15383"]/span[2]/label'))
    ).click()

    # Select an option from the dropdown (10,000 km)
    select_dropdown_option(driver, "ctl07_ucProcess_ucTopQuestions_qst_15370", "10 000 km")

    # Fill text inputs
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_12535"]'))
    ).send_keys("Kalastajatorpantie 1")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_11634"]'))
    ).send_keys("00330")

    # Submit form
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_btnMiddleStepPrice"]'))
    ).click()

    # Extract results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'MotorBonusBanner__bonusBox___1GCtJ'))
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    details = soup.find("div", class_="MotorBonusBanner__bonusBox___1GCtJ")

    print(details.getText() if details else "Details not found.")

def main():
    driver = setup_driver()

    try:
        fill_form(driver)
        solve_captcha(driver, SITE_KEY, PAGE_URL)
        print("Process completed successfully!")
        second_form(driver)
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        time.sleep(10)
        driver.quit()


if __name__ == "__main__":
    main()
