from datetime import datetime, timedelta
from time import sleep

import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request

last_request = datetime.now()


def write_timetables_to_db(ds100: str, date: datetime) -> None:
    global last_request

    if not model.Station.select().where(model.Station.ds100 == ds100).exists():
        print("ERROR: Station not found:", ds100)
        return
    station = model.Station.get(model.Station.ds100 == ds100)

    print("Current station:", station.name, "| Time:", date)

    # Sent only one request per second, db api is limited to 1 request per second
    while datetime.now() - last_request < timedelta(seconds=1):
        sleep(0.1)
    last_request = datetime.now()

    url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/{station.number}/{date.strftime('%y%m%d')}/{date.strftime('%H')}"
    result = sent_db_api_request(url)
    if not result:
        return

    if "timetable" not in result:
        print("ERROR: No timetable or s found")
        return
    if result["timetable"] is None:
        print("ERROR: Timetable is None")
        return
    if "s" not in result["timetable"]:
        print("ERROR: No s found")
        return

    for train in result["timetable"]["s"]:
        try:
            db_train, _ = model.Train.get_or_create(type=train["tl"]["@c"], number=train["tl"]["@n"])
            db_trip, _ = model.Trip.get_or_create(train=db_train, date=date)
            db_stop, _ = model.Stop.get_or_create(station=station, trip=db_trip, db_id=train["@id"])
            if "ar" in train:
                db_stop.arrival = datetime.strptime(train["ar"]["@pt"], "%y%m%d%H%M")
            if "dp" in train:
                db_stop.departure = datetime.strptime(train["dp"]["@pt"], "%y%m%d%H%M")
            db_stop.save()
        except Exception as e:
            print(e)


def main():
    model.db.connect()

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT", "FF", "KD", "MA", "NN", "TBI", "UE", "TU", "RM",
                "FKW", "HH", "LL"]
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
