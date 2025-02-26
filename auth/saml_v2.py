from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import getpass
import json
import time


class NEU_SAML_Authenticator:
    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()
        self.driver_options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Chrome(options=self.driver_options)

    def authenticate(self, url, username, password):
        print(f"[INFO] Navigating to {url}")
        self.driver.get(url)

        # Debug: Print initial page source
        print("[DEBUG] Initial page source (first 1000 chars):")
        print(self.driver.page_source[:1000])

        # Wait for the login form
        form = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        print("[INFO] Found login form")

        # Fill in login credentials
        form.find_element(By.NAME, "j_username").send_keys(username)
        form.find_element(By.NAME, "j_password").send_keys(password)
        form.find_element(By.NAME, "_eventId_proceed").click()
        print("[INFO] Submitted login credentials")

        # Debug: Print page source after submitting credentials
        time.sleep(2)  # Give it some time to load
        print("[DEBUG] Page source after submitting credentials (first 1000 chars):")
        print(self.driver.page_source[:1000])

        # Wait for the Duo iframe
        iframe = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        print("[INFO] Found Duo iframe, switching to it")
        self.driver.switch_to.frame(iframe)

        # Click "Remember me" and send push notification
        try:
            remember_me_checkbox = self.driver.find_element(By.NAME, "dampen_choice")
            if not remember_me_checkbox.is_selected():
                remember_me_checkbox.click()
            print("[INFO] Selected 'Remember me for 30 days'")

            # Click the "Send Me a Push" button
            push_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send Me a Push')]")
            push_button.click()
            print("[INFO] Sent Duo push request")
        except Exception as e:
            print(f"[ERROR] Error interacting with Duo iframe: {e}")
            return None

        # Switch back to the main content
        self.driver.switch_to.default_content()

        # Wait for authentication to complete
        time.sleep(10)  # Adjust based on Duo response time

        # Debug: Print page source after Duo authentication
        print("[DEBUG] Page source after Duo auth (first 1000 chars):")
        print(self.driver.page_source[:1000])

        # Get cookies
        cookies = self.driver.get_cookies()
        print("[INFO] Extracted cookies:", cookies)

        # Store cookies in a file
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        print("[INFO] Cookies saved to cookies.json")

        return cookies

    def close(self):
        self.driver.quit()
        print("[INFO] WebDriver session closed.")


def main():
    url = "https://www.applyweb.com/eval/shibboleth/neu/36892"
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    auth = NEU_SAML_Authenticator()
    auth_cookie = auth.authenticate(url, username, password)

    if auth_cookie:
        print("[SUCCESS] Authentication completed successfully!")
    else:
        print("[FAIL] Authentication failed.")

    auth.close()


if __name__ == "__main__":
    main()
