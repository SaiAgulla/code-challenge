import os
from datetime import datetime
from tqdm import tqdm
from sqlalchemy import text
from app import app, db, Weather, WeatherStats, Yield

WX_DIR = "wx_data"
YLD_FILE = "yld_data/US_corn_grain_yield.txt"

# Ingest Weather Data
def ingest_weather():
    print("Starting weather ingestion...")
    count = 0

    files = os.listdir(WX_DIR)
    for fname in tqdm(files, desc="Weather files"):
        station = fname.replace(".txt", "")
        with open(os.path.join(WX_DIR, fname)) as f:
            for line in f:
                d, tmax, tmin, prcp = line.split()
                rec = Weather(
                    station_id=station,
                    date=datetime.strptime(d, "%Y%m%d").date(),
                    max_temp_c=None if tmax == "-9999" else int(tmax) / 10,
                    min_temp_c=None if tmin == "-9999" else int(tmin) / 10,
                    precipitation_mm=None if prcp == "-9999" else int(prcp) / 10,
                )
                db.session.merge(rec)
                count += 1

    db.session.commit()
    print(f"Weather ingestion complete — {count:,} rows ingested\n")



# Ingest Yield Data
def ingest_yield():
    print("Starting yield ingestion...")
    with open(YLD_FILE) as f:
        for line in tqdm(f, desc="Yield records"):
            year, value = line.split()
            db.session.merge(Yield(year=int(year), total_yield=int(value)))

    db.session.commit()
    print("Yield ingestion complete\n")



# Calculate Weather Stats
def calculate_stats():
    print("Calculating yearly weather statistics...")
    db.session.query(WeatherStats).delete()

    rows = db.session.execute(text("""
        SELECT
            station_id,
            strftime('%Y', date) AS year,
            AVG(max_temp_c),
            AVG(min_temp_c),
            SUM(precipitation_mm) / 10.0
        FROM weather
        GROUP BY station_id, year
    """))

    for r in tqdm(rows, desc="Station/year aggregates"):
        db.session.add(WeatherStats(
            station_id=r[0],
            year=int(r[1]),
            avg_max_temp_c=r[2],
            avg_min_temp_c=r[3],
            total_precip_cm=r[4]
        ))

    db.session.commit()
    print("Statistics calculation complete\n")

# Main Execution
if __name__ == "__main__":
    with app.app_context():
        ingest_weather()
        ingest_yield()
        calculate_stats()
        print("All ingestion steps completed successfully.")
