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
    db_stations = []

    for station in stations:
        # print(station)
        # model.Station.get_or_create(name=station["@name"], number=station["@eva"], ds100=station["@ds100"])
        db_stations.append({
            "name": station["@name"],
            "number": station["@eva"],
            "ds100": station["@ds100"]})
    
    with model.db.atomic():
        # TODO: Don't ignore conflicts, update row instead
        model.Station.insert_many(db_stations).on_conflict_ignore().execute()

def main():
    model.connect()
    insert_stations_to_db()

if __name__ == "__main__":
    main()
