from datetime import datetime, timedelta
from time import sleep

import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request

last_request = datetime.now()


def write_timetables_to_db(ds100: str) -> None:
    global last_request

    station = model.Station.get(model.Station.ds100 == ds100)
    print("Current station:", station.name)
    while datetime.now() - last_request < timedelta(seconds=1):
        sleep(0.1)
    last_request = datetime.now()

    url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/fchg/{station.number}"
    result = sent_db_api_request(url)
    if not result:
        return

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

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT", "FF", "KD", "MA", "NN", "TBI", "UE", "TU", "RM",
                "FKW", "HH", "LL"]

    for station in stations:
        write_timetables_to_db(station)


if __name__ == "__main__":
    main()
