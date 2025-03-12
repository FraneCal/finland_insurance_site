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


chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless") 
chrome_options.add_argument("--no-sandbox") 
chrome_options.add_argument("--disable-dev-shm-usage") 
 
driver = webdriver.Chrome(options=chrome_options)

API_KEY = "6eac18b9d70d016d0dcdaf58772e934b"
driver.maximize_window()
driver.get("https://www.if.fi/henkiloasiakkaat/vakuutukset/autovakuutus")

try:
    accept_cookies = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
    accept_cookies.click()
except TimeoutException:
    print("No accept cookies button found.")

input_field_1 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11631_24c590b5-a868-4504-9612-6aaa08f75aa2"]')))
input_field_1.click()
input_field_1.send_keys("LSO-589")

input_field_2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="qst_11630_9941162d-0136-4489-b0ab-adecca269141"]')))
input_field_2.click()
input_field_2.send_keys("200992-248W")

submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]')))
submit_button.click()

try:
    # Locate the reCAPTCHA iframe by title
    recaptcha_iframe = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
    )

    # Switch to the reCAPTCHA iframe
    driver.switch_to.frame(recaptcha_iframe)

    # Locate and click the reCAPTCHA checkbox
    recaptcha_checkbox = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
    )
    recaptcha_checkbox.click()

    # Switch back to the default content
    driver.switch_to.default_content()

    print("reCAPTCHA checkbox clicked successfully!")

except TimeoutException:
    print("reCAPTCHA not found or clickable.")

try:
    submit_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="entryFormSubmit"]')))
    submit_button.click()   
except TimeoutException:
    print("It is not needed to click the Submit button again.")

element_on_next_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl07_ucProcess_ucTopQuestions_qst_12535"]')))
element_on_next_page.click()
element_on_next_page.send_keys("I don't have an adress")

time.sleep(2)

driver.execute_script("window.scrollTo(0, document.body.scrollTop);")

time.sleep(5)
