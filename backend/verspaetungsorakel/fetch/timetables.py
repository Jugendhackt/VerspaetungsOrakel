from datetime import datetime, timedelta

from peewee import IntegrityError

from verspaetungsorakel.logger import log
import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request, wait_one_second


def write_timetables_to_db(ds100: str, date: datetime):
    # Sent only one request per second, db api is limited to 1 request per second
    wait_one_second()

    station = model.Station.get_or_none(model.Station.ds100 == ds100)
    if station is None:
        log.warn(f"Station not found in database: {ds100}")
        return

    log.debug(f"Fetching timetable for {station.name} at {date}")

    url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/{station.number}/{date.strftime('%y%m%d')}/{date.strftime('%H')}"
    try:
        result = sent_db_api_request(url)
    except ConnectionError as e:
        log.warn(e)
        return

    if ("timetable" not in result) or (result["timetable"] is None) or ("s" not in result["timetable"]):
        log.warn("No timetable found for this station and time")
        return

    for train in result["timetable"]["s"]:
        if type(train) is str:
            log.warn("Train is string, skipping")
            continue

        db_train, _ = model.Train.get_or_create(type=train["tl"]["@c"], number=train["tl"]["@n"])
        db_trip, _ = model.Trip.get_or_create(train=db_train, date=date)

        try:
            db_stop, _ = model.Stop.get_or_create(station=station, trip=db_trip, db_id=train["@id"])
        except IntegrityError as e:
            log.error(f"DB Integrity Error: {e}")
            continue

        if "ar" in train:
            db_stop.arrival = datetime.strptime(train["ar"]["@pt"], "%y%m%d%H%M")
        if "dp" in train:
            db_stop.departure = datetime.strptime(train["dp"]["@pt"], "%y%m%d%H%M")

        db_stop.save()


def main():
    log.info("Start fetching timetables")

    model.db.connect()

    stations = ["FFLF", "MH", "KK", "RK", "TS", "AH", "BL", "BLT", "FF", "KD", "MA", "NN", "TBI", "UE", "TU", "RM",
                "FKW", "HH", "LL"]
    start = datetime.now() - timedelta(hours=6)
    end = datetime.now() + timedelta(days=1)

    for i, station in enumerate(stations):
        log.info(f"Fetching timetable for {station}, {round(i / len(stations) * 100)}%")

        current = start
        while current < end:
            write_timetables_to_db(station, current)
            current += timedelta(hours=1)

    model.db.close()

    log.info("Done")


if __name__ == "__main__":
    main()
