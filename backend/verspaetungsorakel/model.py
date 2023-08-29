from dotenv import load_dotenv
from peewee import *
import os

from verspaetungsorakel.logger import log

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
    type = CharField(max_length=20)

    class Meta:
        indexes = ((("number", "type"), True),)


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
    arrival = DateTimeField(null=True)
    departure = DateTimeField(null=True)
    arrival_delay = IntegerField(null=True)
    departure_delay = IntegerField(null=True)
    db_id = CharField(unique=True)

    class Meta:
        indexes = ((("station", "arrival", "departure", "trip"), True),)


try:
    db.connect()
    db.create_tables([Train, Trip, Station, Stop])
    db.close()
except Exception as e:
    log.fatal(f"Database Error: {e}")
    exit(1)
