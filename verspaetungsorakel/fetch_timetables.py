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
        print("Current station:", station.name, "| Time:", date)
        global last_request
        while datetime.now() - last_request < timedelta(seconds=1):
            # print("We're too fast!\nWaiting...")
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
            # print(train)
            saved_train = model.Train.get_or_create(type=train["tl"]["@c"], number=train["tl"]["@n"])
            saved_trip = model.Trip.get_or_create(train=saved_train[0], date=date)
            saved_stop = model.Stop.get_or_create(station=station, trip=saved_trip[0], db_id=train["@id"])
            if "ar" in train:
                saved_stop[0].arrival=datetime.strptime(train["ar"]["@pt"], "%y%m%d%H%M")
            if "dp" in train:
                saved_stop[0].departure=datetime.strptime(train["dp"]["@pt"], "%y%m%d%H%M")
            saved_stop[0].save()


def main():
    model.connect()

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT"]
    start = datetime.now() - timedelta(hours=6)
    end = datetime.now() + timedelta(days=1)
    

    for station in stations:
        current = start
        while current < end:
            write_timetables_to_db(station, current)
            current += timedelta(hours=1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Killed!")
        exit(0)
