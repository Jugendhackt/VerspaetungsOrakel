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

def write_timetables_to_db(ds100: str) -> None:
    for station in model.Station.select().where(model.Station.ds100 == ds100):
        print("Current station:", station.name)
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
            f"/db-api-marketplace/apis/timetables/v1/fchg/{eva_no}",
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
        for s in result["timetable"]["s"]:
            try:
                stop = model.Stop.get(model.Stop.db_id == s["@id"])
            except model.DoesNotExist:
                # print("Unknown stop")
                continue

            try:
                actual_arrival = datetime.strptime(s["ar"]["@ct"], "%y%m%d%H%M")
                stop.arrival_delay = (actual_arrival - stop.arrival).total_seconds()
            except KeyError:
                # print("Unknown key lol")
                pass

            try:
                actual_departure = datetime.strptime(s["dp"]["@ct"], "%y%m%d%H%M")
                stop.departure_delay = (actual_departure - stop.departure).total_seconds()
            except KeyError:
                # print("Unknown key lol")
                pass

            stop.save()


def main():
    model.connect()

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT"]

    for station in stations:
        write_timetables_to_db(station)

if __name__ == "__main__":
    main()
