from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import re
from peewee import Value
from playhouse.shortcuts import model_to_dict

import model as model

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/ping")
def ping():
    return "pong", 200


@app.route("/api/submit")
def submit():
    train = request.args.get("train")
    try:
        numbers = re.compile(r'\d+')
        train = int(numbers.findall(train)[0])
    except ValueError:
        return jsonify({"error": "invalid train number"}), 400
    # TODO: ds100
    station = request.args.get("station")

    average_delay = get_delay(station, train)
    last_delays = get_last_delays(station, train)
    arrival, departure = get_stop_time(station, train)

    print({
        "average_delay": average_delay,
        "arrival": arrival,
        "departure": departure,
        "last_delays": last_delays})
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
        response = [{"date": stop.arrival.date().strftime('%Y-%m-%d'), "delay": round(stop.arrival_delay / 60, 2)} for stop
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


@app.route("/api/trains")
def list_trains():
    number: str = request.args.get("number", "")

    trains = []
    for train in model.Train.select().where(model.Train.number.like(f"{number}%")):
        trains.append(model_to_dict(train))

    return jsonify(trains), 200


@app.route("/api/stations")
def list_stations():
    name = request.args.get("name", "")

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


def main():
    model.connect()
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
