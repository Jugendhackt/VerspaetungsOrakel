from peewee import fn
import http.client
import os
import xmltodict

import model

DB_API_ID = os.getenv("DB_API_ID")
DB_API_KEY = os.getenv("DB_API_KEY")

def get_stations(query: str) -> str:
    conn = http.client.HTTPSConnection("apis.deutschebahn.com")

    headers = {
        "DB-Client-Id": DB_API_ID,
        "DB-Api-Key": DB_API_KEY,
        "accept": "application/xml"
    }

    conn.request(
        "GET",
        f"/db-api-marketplace/apis/timetables/v1/station/{query}",
        headers=headers
    )

    res = conn.getresponse()
    data = res.read()

    if res.status != 200:
        print(f"Error {res.status} accessing the API")
        exit(1)

    return xmltodict.parse(data.decode("utf-8"))

def insert_stations_to_db() -> None:
    stations = get_stations("*")["stations"]["station"]

    for station in stations:
        # print(s)
        model.Station.replace(name=station["@name"], number=station["@eva"], ds100=station["@ds100"]).execute()

def main():
    model.connect()
    insert_stations_to_db()

if __name__ == "__main__":
    main()
