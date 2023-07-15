import datetime

from peewee import SqliteDatabase

import verspaetungsorakel.main as main
import verspaetungsorakel.model as model


def test_get_delay():
    test_db = SqliteDatabase(":memory:")
    tables = [model.Stop, model.Station, model.Train, model.Trip]
    test_db.bind(tables)
    test_db.connect()
    test_db.create_tables(tables)

    station = model.Station.create(name="Aadorf", number=8506013, ds100="OSADF")
    train = model.Train.create(number=123, type="IC")
    trip = model.Trip.create(train=train, date=datetime.date.today())

    model.Stop.create(
        station=station,
        trip=trip,
        arrival="2019-01-01 12:30:45",
        departure="2019-01-01 12:35:45",
        arrival_delay=3,
        departure_delay=1
    )
    assert main.get_delay(8506013, 123) == 0

    model.Stop.create(
        station=station,
        trip=trip,
        arrival=datetime.datetime.now() - datetime.timedelta(minutes=10),
        departure=datetime.datetime.now() - datetime.timedelta(minutes=5),
        arrival_delay=3,
        departure_delay=1
    )
    assert main.get_delay(8506013, 123) == 3

    model.Stop.create(
        station=station,
        trip=trip,
        arrival=datetime.datetime.now() - datetime.timedelta(minutes=30),
        departure=datetime.datetime.now() - datetime.timedelta(minutes=20),
        arrival_delay=5,
        departure_delay=1
    )

    assert main.get_delay(8506013, 123) == 4

    test_db.close()
