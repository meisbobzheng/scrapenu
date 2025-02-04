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
            print(input.attrs['name'] + ": " + input.attrs['value'])

        # populate form inputs
        input_data['j_username'] = username
        input_data['j_password'] = password
        input_data['_eventId_proceed'] = ''

        # post to form action
        print("posting to " + new_base_url + action)
        response = self.session.post(new_base_url + action, data=input_data)
        print(response.text)


        
new_auth = NEU_SAML_Authenticator()
result = new_auth.authenticate("https://www.applyweb.com/eval/shibboleth/neu/36892", "test", "password")