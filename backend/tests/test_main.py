from peewee import SqliteDatabase

import verspaetungsorakel.model as model
import verspaetungsorakel.main as main


def test_get_delay():
    test_db = SqliteDatabase(":memory:")
    tables = [model.Stop, model.Station, model.Train, model.Trip]
    test_db.bind(tables)
    test_db.connect()
    test_db.create_tables(tables)

    station = model.Station.create(name="Aadorf", number=8506013, ds100="OSADF")
    train = model.Train.create(number=123, type="IC")
    trip = model.Trip.create(train=train, date="2019-01-01")

    # assert model.Trip.select().where(model.Trip.train.number == 123).count() == 1

    model.Stop.create(
        station=station,
        trip=trip,
        arrival="2019-01-01 12:30:45",
        departure="2019-01-01 12:35:45",
        arrival_delay=3,
        departure_delay=1
    )
    assert main.get_delay(8506013, 123) == 3

    model.Stop.create(
        station=station,
        trip=trip,
        arrival="2019-01-01 13:30:45",
        departure="2019-01-01 13:35:45",
        arrival_delay=5,
        departure_delay=1
    )

    assert main.get_delay(8506013, 123) == 4

    test_db.close()
