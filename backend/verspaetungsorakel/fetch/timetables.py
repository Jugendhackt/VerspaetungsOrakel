from datetime import datetime, timedelta
from time import sleep

from peewee import IntegrityError

import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request

last_request = datetime.now()


def write_timetables_to_db(ds100: str, date: datetime):
    global last_request

    if not model.Station.select().where(model.Station.ds100 == ds100).exists():
        print("ERROR: Station not found:", ds100)
        return
    station = model.Station.get(model.Station.ds100 == ds100)

    print(f"Current station: {station.name} | Time: {date}")

    # Sent only one request per second, db api is limited to 1 request per second
    while datetime.now() - last_request < timedelta(seconds=1):
        sleep(0.1)
    last_request = datetime.now()

    url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/{station.number}/{date.strftime('%y%m%d')}/{date.strftime('%H')}"
    try:
        result = sent_db_api_request(url)
    except ConnectionError as e:
        print("ERROR: ", e)
        return

    if ("timetable" not in result) or (result["timetable"] is None) or ("s" not in result["timetable"]):
        print("WARN: No timetable found for this station and time")
        return

    for train in result["timetable"]["s"]:
        if type(train) is str:
            print("WARN: Train is string, skipping")
            continue

        db_train, _ = model.Train.get_or_create(type=train["tl"]["@c"], number=train["tl"]["@n"])
        db_trip, _ = model.Trip.get_or_create(train=db_train, date=date)

        try:
            db_stop, _ = model.Stop.get_or_create(station=station, trip=db_trip, db_id=train["@id"])
        except IntegrityError as e:
            print("DB Integrity Error: ", e)
            continue

        if "ar" in train:
            db_stop.arrival = datetime.strptime(train["ar"]["@pt"], "%y%m%d%H%M")
        if "dp" in train:
            db_stop.departure = datetime.strptime(train["dp"]["@pt"], "%y%m%d%H%M")

        db_stop.save()


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

    model.db.close()


if __name__ == "__main__":
    main()
