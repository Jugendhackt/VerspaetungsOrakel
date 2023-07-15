from flask import Flask, request, jsonify
from peewee import fn

import verspaetungsorakel.model as model

app = Flask(__name__)


@app.route("/api/submit")
def submit():
    train = request.args.get("train")
    station = request.args.get("station")

    average_delay = model.Stop.select(fn.AVG(model.Stop.departure_delay)).where(
        model.Stop.station.name == station,
        model.Stop.trip.train.number == train
    ).first()

    return jsonify({"average_delay": average_delay}), 200


# @app.route("/api/stations")
def main():
    model.connect()
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
