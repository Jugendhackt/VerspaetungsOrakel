from contextlib import asynccontextmanager
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pony.orm import db_session, select, desc
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from verspaetungsorakel.bahn import write_timetables_to_database, get_delays, write_stations_to_database
from verspaetungsorakel.database import Station, Train, Stop

VERSION = "0.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_data, "cron", hour="7,15,23")
    scheduler.start()

    yield

    scheduler.shutdown()


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def update_data():
    write_stations_to_database()
    write_timetables_to_database()
    get_delays()


@app.get("/")
@limiter.limit("60/minute")
def index(request: Request, station: str = None, train: str = None):
    if not station and not train:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "version": VERSION,
            "station_search": station,
            "train_search": train,
            "status": "no_search"
        })

    t_type, t_number = upack_train(train)

    with db_session:
        db_train = Train.get(number=t_number, type=t_type)
        if not db_train:
            raise HTTPException(status_code=404, detail="Train not found")
        db_station = Station.get(name=station)
        if not db_station:
            raise HTTPException(status_code=404, detail="Station not found")

        db_stop = Stop.select(lambda s: s.station == db_station and s.trip.train == db_train).order_by(
            lambda s: desc(s.trip.date)).first()
        if not db_stop:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "version": VERSION,
                "station_search": station,
                "train_search": train,
                "status": "no_data",
            })

        delays = select(
            ((s.arrival_delay + s.departure_delay) / 2, s.trip.date)
            for s in Stop
            if s.station == db_station and s.trip.train == db_train and
            s.trip.date >= date.today() - timedelta(days=30)
        ).order_by(2)[:]
        # Temp. Replace None with 0 in delays to prevent chart draw failure
        delays = list(map(lambda d: (0, d[1]) if d[0] is None else (d[0], d[1]), delays))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": VERSION,
        "stop": db_stop,
        "station": db_station,
        "delays": delays,
        "train": db_train,
        "station_search": station,
        "train_search": train,
        "status": "search"
    })


@app.get("/api/v1/ping")
def ping():
    return "pong"


@app.get("/api/v1/stations")
@limiter.limit("60/minute")
def get_stations(station: str, request: Request):
    with db_session:
        stations = to_dicts(Station.select(lambda s: station in s.name)[:])
    return templates.TemplateResponse("api/stations_search.html", {"request": request, "stations": stations})


@app.get("/api/v1/trains")
@limiter.limit("60/minute")
def get_trains(train: str, request: Request):
    t_type, t_number = upack_train(train)

    with db_session:
        trains = to_dicts(Train.select(lambda t: t_number in t.number and t_type in t.type).limit(100)[:])
    return templates.TemplateResponse("api/trains_search.html", {"request": request, "trains": trains})


def to_dicts(entities: list) -> list:
    return [e.to_dict() for e in entities]


def upack_train(train: str) -> tuple:
    t_args = train.split(" ")
    if len(t_args) != 2:
        raise HTTPException(status_code=400, detail="Invalid train number")

    t_type = t_args[0].upper()
    t_number = t_args[1]

    return t_type, t_number
