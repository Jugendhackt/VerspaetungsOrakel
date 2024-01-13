import sqlite3
from datetime import date, datetime
from pathlib import Path

from pony.orm import *

Path("database").mkdir(parents=True, exist_ok=True)

DATABASE = "./../database/database.db"
db = Database()


@db.on_connect(provider="sqlite")
def sqlite_wal_mode(db, connection: sqlite3.Connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")


class Train(db.Entity):
    number = Required(str)
    type = Required(str)

    PrimaryKey(number, type)

    trips = Set(lambda: Trip)


class Station(db.Entity):
    name = PrimaryKey(str)

    stops = Set(lambda: Stop)


class Trip(db.Entity):
    train = Required(Train)
    date = Required(date)

    stops = Set(lambda: Stop)

    PrimaryKey(train, date)


class Stop(db.Entity):
    station = Required(Station)
    trip = Required(Trip)
    arrival = Optional(datetime)
    departure = Optional(datetime)
    arrival_delay = Optional(int)
    departure_delay = Optional(int)
    db_id = Required(str)

    PrimaryKey(station, db_id)


db.bind(provider="sqlite", filename=DATABASE, create_db=True)
db.generate_mapping(create_tables=True)
