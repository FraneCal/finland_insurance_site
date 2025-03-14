import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import RecaptchaV2ProxylessRequest

API_KEY = "YOUR API KEY"
WEBSITE_URL = "https://www.google.com/recaptcha/api2/demo"
WEBSITE_KEY = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"

client_options = ClientOptions(api_key=API_KEY)
cap_monster_client = CapMonsterClient(options=client_options)

async def solve_captcha():
    recaptcha_request = RecaptchaV2ProxylessRequest(websiteUrl=WEBSITE_URL, websiteKey=WEBSITE_KEY)
    result = await cap_monster_client.solve_captcha(recaptcha_request)
    return result['gRecaptchaResponse']

async def main():
    try:
        driver = webdriver.Chrome()
        driver.get(WEBSITE_URL)

        await asyncio.sleep(5)

        responses = await solve_captcha()

        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{responses}";')

        driver.find_element(By.ID, 'recaptcha-demo-submit').click()

        await asyncio.sleep(10)

    except Exception as e:
        print('Error:', e)
    finally:
        driver.quit()

asyncio.run(main())
