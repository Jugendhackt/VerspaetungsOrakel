from os import getenv
from time import sleep
from datetime import datetime, timedelta

import requests
import xmltodict
from dotenv import load_dotenv

load_dotenv()
DB_API_ID = getenv("DB_API_ID")
DB_API_KEY = getenv("DB_API_KEY")


def sent_db_api_request(url: str) -> dict | None:
    headers = {
        "DB-Client-Id": DB_API_ID,
        "DB-Api-Key": DB_API_KEY,
        "Accept": "application/xml"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"ERROR: {response.status_code} accessing the API")
        raise ConnectionError(f"ERROR {response.status_code} accessing the API")

    return xmltodict.parse(response.text)


last_request = datetime.now()


def wait_one_second():
    global last_request

    while datetime.now() - last_request < timedelta(seconds=1):
        sleep(0.05)
    last_request = datetime.now()
