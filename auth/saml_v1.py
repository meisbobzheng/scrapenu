import requests
# import json
# import time
from bs4 import BeautifulSoup
# from urllib.parse import urljoin
import sys
import getpass
from playwright.sync_api import sync_playwright

# takes in url
# returns verified SAML cookies

class NEU_SAML_Authenticator:
    def __init__(self):
        self.session = requests.Session()

    def authenticate(self, url, username, password):
        # Initial request
        response = self.session.get(url)
        
        # Build form data
        init_data = {
            'shib_idp_ls_supported': 'true',
            'shib_idp_ls_success.shib_idp_session_ss': 'true',
            'shib_idp_ls_success.shib_idp_persistent_ss': 'true',
            '_eventId_proceed': ''
        }
        
        # post to redirected URL
        print("redirected to: " + response.url)
        response = self.session.post(response.url, data=init_data)
        new_base_url = response.url.rsplit('/idp', 1)[0]
        #print("resposne url: " + new_base_url)
        #print(response.text)

        # look for form in response
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')

        if form is None:
            print("No form found")
            return None
        else :
            print("Form found")
            #print(form)

        # get form action
        action = form.attrs['action']
        print("action: " + action)

        # get form inputs
        inputs = form.find_all('input')
        input_data = {}
        for input in inputs:
            input_data[input.attrs['name']] = input.attrs['value']
            #print(input.attrs['name'] + ": " + input.attrs['value'])

        # populate form inputs
        input_data['j_username'] = username
        input_data['j_password'] = password
        input_data['_eventId_proceed'] = ''

        # # post to form action
        # print("posting to " + new_base_url + action)
        response = self.session.post(new_base_url + action, data=input_data)
        # print(response.text)

        # find the saml iframe
        soup = BeautifulSoup(response.text, 'html.parser')
        iframe = soup.find('iframe', id='duo_iframe')

        if not iframe:
            print("No iframe found")
            return None

        print("iframe found")

        # use normal requests
        # dont need to be using playwright
        # refer to the screenshot!!

        # with open('auth/duo_frame.html', 'w') as f:
        #     f.write(response.text)
        #     f.close()

        duo_host = iframe.attrs['data-host']
        duo_action = iframe.attrs['data-post-action']
        sig_request = iframe.attrs['data-sig-request'].split(':APP')[0]

        print ("duo_host: " + duo_host)
        print ("duo_action: " + duo_action)
        print ("sig_request: " + sig_request)
        print("new base url: " + new_base_url)


        iframe_src = 'https://' + duo_host + '/frame/web/v1/auth?tx=' + sig_request + '&parent=' + new_base_url + duo_action + '&v=2.6'

        print('iframe src: ' + iframe_src)

        auth_cookie = None

        with sync_playwright() as p: 
            browser = p.chromium.launch(headless = True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(iframe_src, wait_until='networkidle')

            # Get all script URLs
            script_urls = page.evaluate("[...document.querySelectorAll('script[src]')].map(s => s.src)")
            print("Scripts Loaded:", script_urls)

            with open('auth/duo_frame.html', 'w') as f:
                f.write(page.content())
                f.close()

            page.get_by_role("button", name="Send Me a Push").click()


            browser.close()
        
        if not auth_cookie:
            print("No auth cookie found")
            return None
        
        return auth_cookie

        



# new_auth = NEU_SAML_Authenticator()
# result = new_auth.authenticate("https://www.applyweb.com/eval/shibboleth/neu/36892", "test", "password")

def main():
    # url = input("Enter URL: ")
    url = 'https://www.applyweb.com/eval/shibboleth/neu/36892'
    username = input ("Enter username: ")
    password = getpass.getpass("Enter password: ")

    new_auth = NEU_SAML_Authenticator()
    auth_cookie = new_auth.authenticate(url, username, password)
    print(auth_cookie)


if __name__ == "__main__":
    main()