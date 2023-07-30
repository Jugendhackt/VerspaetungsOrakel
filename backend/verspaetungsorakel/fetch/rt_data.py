from datetime import datetime

from rich.progress import track

import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request, wait_one_second


def write_timetables_to_db(ds100: str):
    # Sent only one request per second, db api is limited to 1 request per second
    wait_one_second()

    station = model.Station.get_or_none(model.Station.ds100 == ds100)
    if station is None:
        print("ERROR: Station not found:", ds100)
        return
    print("Current station:", station.name)

    url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/fchg/{station.number}"
    try:
        result = sent_db_api_request(url)
    except ConnectionError as e:
        print(e)
        return

    for s in result["timetable"]["s"]:
        stop = model.Stop.get_or_none(model.Stop.db_id == s["@id"])
        if stop is None:
            # print("WARN: Stop not found in database:", s["@id"])
            continue

        try:
            actual_arrival = datetime.strptime(s["ar"]["@ct"], "%y%m%d%H%M")
            stop.arrival_delay = (actual_arrival - stop.arrival).total_seconds()
        except KeyError:
            pass

        try:
            actual_departure = datetime.strptime(s["dp"]["@ct"], "%y%m%d%H%M")
            stop.departure_delay = (actual_departure - stop.departure).total_seconds()
        except KeyError:
            pass

        stop.save()


def main():
    model.connect()

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT", "FF", "KD", "MA", "NN", "TBI", "UE", "TU", "RM",
                "FKW", "HH", "LL"]

    for station in track(stations):
        write_timetables_to_db(station)


if __name__ == "__main__":
    main()
