import os

import verspaetungsorakel.model as model
from verspaetungsorakel.fetch.utils import sent_db_api_request

DB_API_ID = os.getenv("DB_API_ID")
DB_API_KEY = os.getenv("DB_API_KEY")


def insert_stations_to_db() -> None:
    url = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/*"
    result = sent_db_api_request(url)
    if not result:
        return

    stations = result["stations"]["station"]
    # db_stations = []

    for station in stations:
        # print(station)
        model.Station.get_or_create(name=station["@name"], number=station["@eva"], ds100=station["@ds100"])
        # db_stations.append({
        #     "name": station["@name"],
        #     "number": station["@eva"],
        #     "ds100": station["@ds100"]})

    # with model.db.atomic():
    #     # TODO: Don't ignore conflicts, update row instead
    #     model.Station.insert_many(db_stations).on_conflict_ignore().execute()


def main():
    model.connect()
    insert_stations_to_db()


if __name__ == "__main__":
    main()
