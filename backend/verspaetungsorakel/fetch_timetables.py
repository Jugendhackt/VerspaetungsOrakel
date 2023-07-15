from peewee import fn
import http.client
import os
import xmltodict
from datetime import datetime, timedelta
from time import sleep

import model

DB_API_ID = os.getenv("DB_API_ID")
DB_API_KEY = os.getenv("DB_API_KEY")
last_request = datetime.now()

def write_timetables_to_db(ds100: str, date: datetime) -> None:
    for station in model.Station.select().where(model.Station.ds100 == ds100):
        global last_request
        while datetime.now() - last_request < timedelta(seconds=1):
            print("We're too fast!\nWaiting...")
            sleep(0.1)
        last_request = datetime.now()
        eva_no = station.number
        
        conn = http.client.HTTPSConnection("apis.deutschebahn.com")

        headers = {
            "DB-Client-Id": DB_API_ID,
            "DB-Api-Key": DB_API_KEY,
            "accept": "application/xml"
        }

        conn.request(
            "GET",
            f"/db-api-marketplace/apis/timetables/v1/plan/{eva_no}/{date.strftime('%y%m%d')}/{date.strftime('%H')}",
            headers=headers
        )

        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            print(f"Error {res.status} accessing the API")
            print(data)
            # exit(1)
            return

        result = xmltodict.parse(data.decode("utf-8"))
        for train in result["timetable"]["s"]:
            saved_train = model.Train.get_or_create(type=train["tl"]["@c"], number=train["tl"]["@n"])
            saved_trip = model.Trip.get_or_create(train=saved_train[0], date=date)
            model.Stop.get_or_create(station=station, trip=saved_trip[0], arrival=datetime.strptime(train["ar"]["@pt"], "%y%m%d%H%M"), departure=datetime.strptime(train["dp"]["@pt"], "%y%m%d%H%M"))
            print(train)


def main():
    model.connect()

    stations = ["FFLF", "MH"]
    start = datetime.now() - timedelta(hours=6)
    end = datetime.now() + timedelta(days=2)
    current = start

    for station in stations:
        while current < end:
            write_timetables_to_db("FFLF", current)
            current += timedelta(hours=1)

if __name__ == "__main__":
    main()
