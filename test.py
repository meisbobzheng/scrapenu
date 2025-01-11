import requests

def main():
    r = requests.get("https://neu.uachieve.com/selfservice/audit/create.html")
    print ('text', r.text)
    print ('status', r.status_code)
    print ('url', r.url)
    print ('history', r.history)

if __name__ == "__main__":
    main()