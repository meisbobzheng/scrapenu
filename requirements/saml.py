import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# takes in url
# returns verified SAML cookies

class NEU_SAML_Authenticator:
    def __init__(self):
        self.session = requests.Session()

    def authenticate(self, url, username, password):
        # Initial request
        response = self.session.get(url)
        
        # Get the redirected URL as base
        base_url = response.url.rsplit('/', 1)[0]
        
        # Build form data
        init_data = {
            'shib_idp_ls_supported': 'true',
            'shib_idp_ls_success.shib_idp_session_ss': 'true',
            'shib_idp_ls_success.shib_idp_persistent_ss': 'true',
            '_eventId_proceed': ''
        }
        
        # Post to redirected URL
        response = self.session.post(response.url, data=init_data)
        print("base_url: " + base_url)
        print(response.text)
        
        
new_auth = NEU_SAML_Authenticator()
result = new_auth.authenticate("https://www.applyweb.com/eval/shibboleth/neu/36892", "test", "password")