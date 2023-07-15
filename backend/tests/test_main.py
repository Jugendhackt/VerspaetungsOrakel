import datetime

from peewee import SqliteDatabase

import verspaetungsorakel.main as main
import verspaetungsorakel.model as model


def test_get_last_delays():
    test_db = SqliteDatabase(":memory:")
    tables = [model.Stop, model.Station, model.Train, model.Trip]
    test_db.bind(tables)
    test_db.connect()
    test_db.create_tables(tables)

    station = model.Station.create(name="Aadorf", number=8506013, ds100="OSADF")
    train = model.Train.create(number=123, type="IC")

    stops = [
        [datetime.datetime.now() - datetime.timedelta(days=1), 1],
        [datetime.datetime.now() - datetime.timedelta(days=2), 2],
        [datetime.datetime.now() - datetime.timedelta(days=3), 3],
        [datetime.datetime.now() - datetime.timedelta(days=4), 4],
    ]
    for stop in stops:
        trip = model.Trip.create(train=train, date=stop[0].date())
        model.Stop.create(
            station=station,
            trip=trip,
            arrival=stop[0] + datetime.timedelta(minutes=10),
            departure=stop[0] + datetime.timedelta(minutes=15),
            arrival_delay=stop[1],
            departure_delay=0
        )

    print(main.get_last_delays(8506013, 123))

    delays = main.get_last_delays(8506013, 123)
    assert delays[0]["date"] == (datetime.datetime.now() - datetime.timedelta(days=4)).date().strftime('%Y-%m-%d')
    assert delays[1]["delay"] == 3

    test_db.close()


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
