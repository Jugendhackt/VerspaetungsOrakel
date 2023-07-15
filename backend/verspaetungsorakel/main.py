from flask import Flask, request, jsonify
from flask_cors import CORS
from playhouse.shortcuts import model_to_dict

import verspaetungsorakel.model as model

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/ping")
def ping():
    return "pong", 200


@app.route("/api/submit")
def submit():
    train = request.args.get("train")
    station = request.args.get("station")

    stops = model.Stop.select().where(
        model.Stop.station.number == station,
        model.Stop.trip.train.number == train
    )

    total_delay = 0
    for stop in stops:
        total_delay += stop.arrival_delay

    average_delay = total_delay / len(stops)

    return jsonify({"average_delay": average_delay}), 200


@app.route("/api/stations")
def list_stations():
    name = request.args.get("name", "")

    stations = []
    for station in model.Station.select().where(model.Station.name.contains(name)):
        stations.append(model_to_dict(station))

    return jsonify(stations), 200


def main():
    model.connect()
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
