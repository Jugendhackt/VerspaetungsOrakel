import datetime
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import model as model

TRAIN_REGEX = r"^\d{1,6}$"
STATION_REGEX = r"^[a-zA-Z.\-,() ]{2,32}$|^[A-Z0-9]{1,8}$"
FRONTEND_SERVER = "http://127.0.0.1:5173"

app = Flask(__name__)
cors = CORS(app, origins=FRONTEND_SERVER)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per second"],
    # TODO: change to proper caching instance
    storage_uri="memory://"
)


@app.before_request
def before_request():
    model.db.connect()


@app.after_request
def after_request(response):
    model.db.close()
    return response


@app.route("/ping", methods=["GET"])
@limiter.exempt
def ping():
    return "pong", 200


@app.route("/api/submit", methods=["GET"])
@limiter.limit("20/minute")
def submit():
    train_number = request.args.get("train")
    station_name = request.args.get("station")

    # Validate input
    if not validate(train_number, TRAIN_REGEX):
        return jsonify({"error": "Broken train number"}), 400
    train_number = int(train_number)
    # TODO: ds100
    if not validate(station_name, STATION_REGEX):
        return jsonify({"error": "Broken station name"}), 400

    if not train_exists(train_number):
        return jsonify({"error": "Train not found"}), 404
    if not station_exists(station_name):
        return jsonify({"error": "Station not found"}), 404

    average_delay = get_delay(station_name, train_number)
    last_delays = get_last_delays(station_name, train_number)
    arrival, departure = get_stop_time(station_name, train_number)

    return jsonify({
        "average_delay": average_delay,
        "arrival": arrival,
        "departure": departure,
        "last_delays": last_delays
    }), 200


def get_stop_time(station_name: str, train_number: int):
    station_id = model.Station.select(model.Station.id).where(model.Station.name == station_name).first()
    train_id = model.Train.select(model.Train.id).where(model.Train.number == train_number).first()
    trip_id = model.Trip.select(model.Trip.id).where(
        (model.Trip.train == train_id) &
        (model.Trip.date == datetime.date.today())
    ).first()

    stop = model.Stop.select().where(
        (model.Stop.station == station_id) &
        (model.Stop.trip == trip_id)
    ).first()

    if stop is None:
        return 0, 0

    return stop.arrival, stop.departure


def get_last_delays(station_name: str, train_number: int) -> list[dict]:
    stops = model.Stop.select(model.Stop.arrival_delay, model.Stop.arrival).join(
        model.Trip,
        on=(model.Stop.trip == model.Trip.id)
    ).join(
        model.Train,
        on=(model.Trip.train == model.Train.id)
    ).join(
        model.Station,
        on=(model.Stop.station == model.Station.id)
    ).where(
        (model.Station.name == station_name) &
        (model.Train.number == train_number) &
        # limits average to the last 30 days
        (model.Stop.arrival >= datetime.datetime.now() - datetime.timedelta(days=14))
    ).limit(50)

    try:
        response = [{"date": stop.arrival.date().strftime('%Y-%m-%d'), "delay": round(stop.arrival_delay / 60, 2)} for
                    stop
                    in stops]
    except:
        response = [{"date": stop.arrival.date().strftime('%Y-%m-%d'), "delay": 0} for stop in stops]

    return response


def get_delay(station_name: str, train_number: int) -> float:
    station_id = model.Station.select(model.Station.id).where(model.Station.name == station_name).first()
    train_id = model.Train.select(model.Train.id).where(model.Train.number == train_number).first()
    trip_id = model.Trip.select(model.Trip.id).where(model.Trip.train == train_id).first()

    stops = model.Stop.select().where(
        (model.Stop.station == station_id) &
        (model.Stop.trip == trip_id)
    ).order_by(model.Stop.arrival)

    delays = [stop.arrival_delay for stop in stops]
    try:
        average_delay = round((sum(delays) / len(delays)) / 60, 2)
    except:
        average_delay = 0
    return average_delay


@app.route("/api/trains", methods=["GET"])
@limiter.limit("1/second")
def list_trains():
    number = request.args.get("number", "")

    # Validate input
    if not validate(number, TRAIN_REGEX):
        return jsonify({"error": "Broken train number"}), 400

    trains = list(
        model.Train.select().where(model.Train.number.like(f"{number}%")).dicts()
    )

    return jsonify(trains), 200


@app.route("/api/stations", methods=["GET"])
@limiter.limit("1/second")
def list_stations():
    name = request.args.get("name", "")

    # Validate input
    if not validate(name, STATION_REGEX):
        return jsonify({"error": "Broken station name"}), 400

    pattern = r"^[A-Z0-9]{1,8}$"
    ds100 = bool(re.match(pattern, name))

    station_names = []
    if not ds100:
        stations = model.Station.select(model.Station.name).where(model.Station.name.like(f"{name}%"))
        station_names = [station.name for station in stations]
    if ds100:
        stations = model.Station.select(model.Station.ds100).where(model.Station.ds100.like(f"{name}%"))
        station_names = [station.ds100 for station in stations]

    return jsonify(station_names), 200


def train_exists(train_number: int) -> bool:
    return model.Train.select().where(model.Train.number == train_number).exists()


def station_exists(station_name: str) -> bool:
    return model.Station.select().where(model.Station.name == station_name).exists()


def validate(value: str, pattern: str) -> bool:
    if type(value) != str:
        return False
    if not re.match(pattern, value):
        return False
    return True


def main():
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
