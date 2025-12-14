from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields
from datetime import date

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
api = Api(app, title="Weather API", version="1.0")

# Database Models
class Weather(db.Model):
    __tablename__ = "weather"
    station_id = db.Column(db.String, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    max_temp_c = db.Column(db.Float)
    min_temp_c = db.Column(db.Float)
    precipitation_mm = db.Column(db.Float)


class WeatherStats(db.Model):
    __tablename__ = "weather_stats"
    station_id = db.Column(db.String, primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    avg_max_temp_c = db.Column(db.Float)
    avg_min_temp_c = db.Column(db.Float)
    total_precip_cm = db.Column(db.Float)


class Yield(db.Model):
    __tablename__ = "yield"
    year = db.Column(db.Integer, primary_key=True)
    total_yield = db.Column(db.Integer)


with app.app_context():
    db.create_all()

# API Schemas
weather_model = api.model("Weather", {
    "station_id": fields.String,
    "date": fields.String,
    "max_temp_c": fields.Float,
    "min_temp_c": fields.Float,
    "precipitation_mm": fields.Float,
})

stats_model = api.model("WeatherStats", {
    "station_id": fields.String,
    "year": fields.Integer,
    "avg_max_temp_c": fields.Float,
    "avg_min_temp_c": fields.Float,
    "total_precip_cm": fields.Float,
})

yield_model = api.model("Yield", {
    "year": fields.Integer,
    "total_yield": fields.Integer,
})

# API Endpoints
@api.route("/api/weather")
class WeatherAPI(Resource):
    @api.marshal_list_with(weather_model)
    def get(self):
        q = Weather.query

        station = request.args.get("station_id")
        start = request.args.get("start_date")
        end = request.args.get("end_date")
        page = int(request.args.get("page", 1))
        size = int(request.args.get("page_size", 50))

        if station:
            q = q.filter_by(station_id=station)
        if start:
            q = q.filter(Weather.date >= date.fromisoformat(start))
        if end:
            q = q.filter(Weather.date <= date.fromisoformat(end))

        return q.offset((page - 1) * size).limit(size).all()


@api.route("/api/weather/stats")
class StatsAPI(Resource):
    @api.marshal_list_with(stats_model)
    def get(self):
        q = WeatherStats.query

        station = request.args.get("station_id")
        year = request.args.get("year")
        page = int(request.args.get("page", 1))
        size = int(request.args.get("page_size", 50))

        if station:
            q = q.filter_by(station_id=station)
        if year:
            q = q.filter_by(year=int(year))

        return q.offset((page - 1) * size).limit(size).all()


@api.route("/api/yield")
class YieldAPI(Resource):
    @api.marshal_list_with(yield_model)
    def get(self):
        return Yield.query.order_by(Yield.year).all()

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
