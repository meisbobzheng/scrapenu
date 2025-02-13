import asyncio
import getpass
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import httpx  # Replaces requests with an async library


class NEU_SAML_Authenticator:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def authenticate(self, url, username, password):
        # Initial request
        response = await self.client.get(url)
        
        # Build form data
        init_data = {
            'shib_idp_ls_supported': 'true',
            'shib_idp_ls_success.shib_idp_session_ss': 'true',
            'shib_idp_ls_success.shib_idp_persistent_ss': 'true',
            '_eventId_proceed': ''
        }
        
        print("Redirected to:", response.url)
        response = await self.client.post(response.url, data=init_data)
        new_base_url = response.url.rsplit('/idp', 1)[0]

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')

        if form is None:
            print("No form found")
            return None

        print("Form found")

        action = form.attrs['action']
        inputs = form.find_all('input')
        input_data = {input.attrs['name']: input.attrs.get('value', '') for input in inputs}

        # Populate form inputs
        input_data['j_username'] = username
        input_data['j_password'] = password
        input_data['_eventId_proceed'] = ''

        print("Posting to", new_base_url + action)
        response = await self.client.post(new_base_url + action, data=input_data)

        soup = BeautifulSoup(response.text, 'html.parser')
        iframe = soup.find('iframe')

        if not iframe:
            print("No iframe found")
            return None

        print("Iframe found")

        # Extract iframe properties
        duo_host = iframe.attrs['data-host']
        duo_action = iframe.attrs['data-post-action']
        sig_request = iframe.attrs['data-sig-request']

        print("duo_host:", duo_host)
        print("duo_action:", duo_action)
        print("sig_request:", sig_request)

        duo_url = f"https://{duo_host}{duo_action}"
        print("Duo URL:", duo_url)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)  # Change to False for debugging
            page = await browser.new_page()
            await page.goto(duo_url)

            # Wait for iframe to appear
            await page.wait_for_selector("iframe")

            # Get iframe
            frame = page.frame_locator("iframe")

            # Wait for form inside iframe
            saml_form = frame.locator("form")
            await saml_form.wait_for()

            print(await saml_form.evaluate("element => element.outerHTML"))

            # Fill in username/password if necessary
            await saml_form.locator("input[name='username']").fill(username)
            await saml_form.locator("input[name='password']").fill(password)

            # Click the submit button
            await saml_form.locator("button[type='submit']").click()
            print("SAML form submitted")

            # Wait for response and get cookies
            await page.wait_for_timeout(5000)
            cookies = await page.context.cookies()
            print("Cookies:", cookies)

            await browser.close()

        return cookies


async def main():
    url = input("Enter URL: ")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    new_auth = NEU_SAML_Authenticator()
    result = await new_auth.authenticate(url, username, password)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
