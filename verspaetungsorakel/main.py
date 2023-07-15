from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import datetime
from playhouse.shortcuts import model_to_dict

import verspaetungsorakel.model as model

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ping")
def ping():
    return "pong", 200


@app.route("/api/submit")
def submit():
    train = int(request.args.get("train"))
    station = int(request.args.get("station"))

    average_delay = get_delay(station, train)
    last_delays = get_last_delays(station, train)

    return jsonify({"average_delay": average_delay, "last_delays": last_delays}), 200


def get_last_delays(station_number: int, train_number: int) -> list[dict]:
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
        (model.Station.number == station_number) &
        (model.Train.number == train_number) &
        # limits average to the last 30 days
        (model.Stop.arrival >= datetime.datetime.now() - datetime.timedelta(days=14))
    ).limit(50)

    return [{"date": stop.arrival.date().strftime('%Y-%m-%d'), "delay": stop.arrival_delay} for stop in stops]


def get_delay(station_number: int, train_number: int) -> float:
    stops = model.Stop.select().join(
        model.Trip,
        on=(model.Stop.trip == model.Trip.id)
    ).join(
        model.Train,
        on=(model.Trip.train == model.Train.id)
    ).join(
        model.Station,
        on=(model.Stop.station == model.Station.id)
    ).where(
        (model.Station.number == station_number) &
        (model.Train.number == train_number) &
        # limits average to the last 30 days
        (model.Stop.arrival >= datetime.datetime.now() - datetime.timedelta(days=30))
    )

    delays = [stop.arrival_delay for stop in stops]
    try:
        average_delay = round(sum(delays) / len(delays), 2)
    except ZeroDivisionError:
        average_delay = 0
    return average_delay


@app.route("/api/stations")
def list_stations():
    name = request.args.get("name", "")

    stations = []
    for station in model.Station.select().where(model.Station.name.startswith(name)):
        stations.append(model_to_dict(station))

    # search with ds100 when no station was found
    if len(stations) == 0:
        for station in model.Station.select().where(model.Station.ds100.startswith(name)):
            stations.append(model_to_dict(station))

    return jsonify(stations), 200


def main():
    model.connect()
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
