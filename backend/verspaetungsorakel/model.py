from dotenv import load_dotenv
from peewee import *
import os

load_dotenv()

db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_host = os.getenv("DB_HOST")
db_password = os.getenv("DB_PASSWORD")
db = MySQLDatabase(db_name, user=db_user, host=db_host, password=db_password)


class BaseModel(Model):
    class Meta:
        database = db


class Train(BaseModel):
    id = AutoField()
    number = IntegerField()
    type = TextField()


class Trip(BaseModel):
    id = AutoField()
    train = ForeignKeyField(Train)
    date = DateField()

    class Meta:
        indexes = ((("train", "date"), True),)


class Station(BaseModel):
    id = AutoField()
    name = TextField()
    number = IntegerField(unique=True)
    ds100 = TextField()


class Stop(BaseModel):
    id = AutoField()
    station = ForeignKeyField(Station)
    trip = ForeignKeyField(Trip)
    arrival = DateTimeField()
    departure = DateTimeField()
    arrival_delay = IntegerField()
    departure_delay = IntegerField()

    class Meta:
        indexes = ((("station", "arrival", "departure", "trip"), True),)


def connect():
    try:
        db.connect()
        db.create_tables([Train, Trip, Station, Stop])
    except Exception as e:
        print(e)
        exit(1)
