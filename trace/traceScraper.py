import requests

from bs4 import BeautifulSoup

import re

def main():

    cookies = {'JSESSIONID': '1DB2489F856C5A11EAC41DF269A77924'}

    response = requests.post("https://www.applyweb.com/eval/shibboleth/neu/36892")

    print(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup.prettify())


if __name__ == "__main__":
    main()