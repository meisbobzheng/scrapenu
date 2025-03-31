import requests
import getpass
from bs4 import BeautifulSoup
import re
import requests.cookies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time


class NEU_SAML_Authenticator:
    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()
        self.driver_options.add_argument("--headless")  # Run in headless mode
        self.driver_options.add_argument("User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=self.driver_options)

    def authenticate(self, url, username, password) :

        self.driver.delete_all_cookies()

        print(f"[INFO] Navigating to {url}")
        self.driver.get(url)

        # Debug: Print initial page source
        #print("[DEBUG] Initial page source (first 1000 chars):")
        #print(self.driver.page_source[:1000])

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
        #print("[DEBUG] Page source after submitting credentials (first 1000 chars):")
        #print(self.driver.page_source[:1000])

        # Wait for the Duo iframe
        iframe = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        print("[INFO] Found Duo iframe, switching to it")
        self.driver.switch_to.frame(iframe)

        # Click "Remember me" and send push notification
        try:
            # remember_me_checkbox = self.driver.find_element(By.NAME, "dampen_choice")
            # if not remember_me_checkbox.is_selected():
            #     remember_me_checkbox.click()
            # print("[INFO] Selected 'Remember me for 30 days'")

            # Click the "Send Me a Push" button
            push_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send Me a Push')]")
            push_button.click()
            print("[INFO] Sent Duo push request")
        except Exception as e:
            print(f"[INFO] Already authenticated")
            #return None

        # Switch back to the main content
        self.driver.switch_to.default_content()

        # Wait for authentication to complete
        time.sleep(10)  # Adjust based on Duo response time

        # Debug: Print page source after Duo authentication
        #print("[DEBUG] Page source after Duo auth (first 1000 chars):")
        #print(self.driver.page_source[:1000])

        # Get cookies and turn into normal ass cookie
        ## cookies = self.driver.get_cookies()

        page = self.driver.page_source

        with open("page.html", "w") as f:
            f.write(page)

        # Find and click the Reports dropdown
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "navbar-nav"))
            )
            
            # Find Reports dropdown using a more specific selector
            reports_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='dropdown-toggle' and contains(., 'Reports')]"))
            )
            
            # Use JavaScript to click the element (more reliable for Angular apps)
            self.driver.execute_script("arguments[0].click();", reports_dropdown)
            print("[INFO] Clicked on Reports dropdown")
            
            # Wait for dropdown menu to appear and click on Report Browser
            time.sleep(1)  # Short wait to ensure dropdown is fully open
            
            report_browser = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='reportbrowser']"))
            )
            self.driver.execute_script("arguments[0].click();", report_browser)
            print("[INFO] Selected Report Browser from dropdown")
            
            # Wait for the page to load
            time.sleep(3)
            
            # Get the updated page source after navigation
            updated_page = self.driver.page_source
            with open("report_browser_page.html", "w") as f:
                f.write(updated_page)
            print("[INFO] Saved Report Browser page to report_browser_page.html")
        except Exception as e:
            print(f"[ERROR] Failed to navigate to Reports: {e}")

        # Get cookies and continue with the rest of your code...
        cookies = self.driver.get_cookies()
        print(cookies)

        final_cookie = ""
        
        # take out the cookies we need
        for cookie in cookies:
            cookie_name = cookie['name']
            
            if cookie_name != "_gat":
                final_cookie += cookie_name + "=" + cookie['value'] + "; "
        
        print("[INFO] Extracted cookies")

        # Store cookies in a file
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        print("[INFO] Cookies saved to cookies.json")
        print("[SUCCESS] Authentication and navigation completed successfully!")
        print("[INFO] Final cookie:", final_cookie)

        return cookies, final_cookie

    def close(self):
        self.driver.quit()
        print("[INFO] WebDriver session closed.")

def main():
    url = "https://www.applyweb.com/eval/shibboleth/neu/36892"
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    #auth = NEU_SAML_Authenticator()
    #auth_cookies, cookie_string = auth.authenticate(url, username, password)

    #print(cookie_string)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    })

    session.headers.update({
        "Cookie": "JSESSIONID=47AFBCC72FF56336653A93E83F4C4096; workingTermCookie=d29ya2luZ1Rlcm1Db29raWU6MTk1; _ga=GA1.2.434478740.1743108853; dtCookie=v_4_srv_6_sn_DDA29CCEFF4FB93CC1A968C884F40514_perc_100000_ol_0_mul_1_app-3Ab3e4b7260e3c8b7e_0; _shibsession_6576616c2d6e657568747470733a2f2f636f72702e636f6c6c6567656e65742e636f6d2f73686962626f6c6574682d73702f=_416f705dc6e774ce51796cd9c1c9d14d; BIGipServerp-eval.applyweb.com=671745802.36895.0000; Blaze=Z-roIMT-3p_jlxiJ5G4DPwAprQ0; sdbid=36892; sid=j$XT~RdAA2BWPeIR8tz8UmYPL_9!TV58FTcscJC9*nEtnRpLCSa$0KkKBDBa_b$~uf9VQ5vJM_rbkmFv~uMT8FjcKe^T3L6l!.Hiqqi58EqyDqOZ!*nddYc8Lx4zu0^y; awBrowserCheck=true; _gid=GA1.2.1065395895.1743448100; _gat=1; _ga_L6DBD46RX8=GS1.2.1743448101.3.0.1743448101.60.0.0"
    })

    # for cookie in auth_cookies:
    #     session.cookies.set_cookie(requests.cookies.create_cookie(
    #         name=cookie['name'],
    #         value=cookie['value'],
    #         domain=cookie['domain'],
    #         path=cookie['path'],
    #         secure=cookie['secure'],
    #         #httpOnly=cookie['httpOnly'],
    #         #sameSite=cookie['sameSite']
    #     ))

    response = session.get("https://www.applyweb.com/eval/new/studenthome/details")
    print(response.text)

    #response = session.post("https://www.applyweb.com/eval/new/reportbrowser/evaluatedCourses")
    #print(response.text)


if __name__ == "__main__":
    main()