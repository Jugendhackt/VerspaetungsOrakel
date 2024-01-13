from datetime import date, datetime
from os import getenv

from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper
from deutsche_bahn_api.train import Train
from deutsche_bahn_api.train_changes import TrainChanges
from dotenv import load_dotenv
from pony.orm import db_session

from verspaetungsorakel.database import Stop, Train, Trip, Station

load_dotenv()
DB_API_ID = getenv("DB_API_ID")
DB_API_KEY = getenv("DB_API_KEY")

db_api = ApiAuthentication(DB_API_ID, DB_API_KEY)
if not db_api.test_credentials():
    raise ConnectionError("DB API credentials are not valid")


def datetime_from_train(train: Train | TrainChanges, attribute_name: str) -> datetime | None:
    attribute_value = getattr(train, attribute_name, None)
    if not attribute_value:
        return None

    return datetime.strptime(attribute_value, "%y%m%d%H%M")


def get_important_stations():
    station_helper = StationHelper()
    stations = station_helper.stations_list
    stations = list(filter(lambda s: s.Verkehr == "FV", stations))
    stations = list(filter(lambda s: "Hbf" in s.NAME, stations))

    return stations


def write_stations_to_database():
    with db_session:
        for station in get_important_stations():
            if Station.exists(name=station.NAME):
                continue
            Station(
                name=station.NAME,
            )


def write_timetables_to_database():
    for station in get_important_stations():
        timetable_helper = TimetableHelper(station, db_api)
        for h in range(24):
            try:
                trains = timetable_helper.get_timetable(h)
            except Exception:
                continue

            with db_session:
                for train in trains:
                    if train.train_type not in ["ICE", "IC", "EC"]:
                        continue

                    db_train = Train.get(number=train.train_number, type=train.train_type)
                    if db_train is None:
                        db_train = Train(number=train.train_number, type=train.train_type)

                    today = date.today()
                    db_trip = Trip.get(train=db_train, date=today)
                    if db_trip is None:
                        db_trip = Trip(train=db_train, date=today)

                    # Skip if stop already exists
                    if Stop.exists(db_id=train.stop_id):
                        # log.warning(f"Stop '{train.stop_id}' already in database")
                        continue

                    Stop(
                        station=Station[station.NAME],
                        trip=db_trip,
                        db_id=train.stop_id,
                        arrival=datetime_from_train(train, "arrival"),
                        departure=datetime_from_train(train, "departure")
                    )


def get_delays():
    for station in get_important_stations():
        timetable_helper = TimetableHelper(station, db_api)
        for h in range(24):
            try:
                trains = timetable_helper.get_timetable(h)
            except Exception:
                continue
            try:
                trains_with_changes = timetable_helper.get_timetable_changes(trains)
            except KeyError:
                continue

            with db_session:
                db_station = Station[station.NAME]

                for train in trains_with_changes:
                    db_stop = Stop.get(db_id=train.stop_id, station=db_station)
                    if db_stop is None:
                        continue

                    train_changes = train.train_changes
                    new_arrival = datetime_from_train(train_changes, "arrival")
                    new_departure = datetime_from_train(train_changes, "departure")

                    if db_stop.arrival and new_arrival:
                        db_stop.arrival_delay = int(round((new_arrival - db_stop.arrival).total_seconds() / 60, 0))
                    if db_stop.departure and new_departure:
                        db_stop.departure_delay = int(
                            round((new_departure - db_stop.departure).total_seconds() / 60, 0))


if __name__ == "__main__":
    write_stations_to_database()

    write_timetables_to_database()
    get_delays()
