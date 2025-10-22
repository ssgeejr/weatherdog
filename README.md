# WeatherDog - Python + MySQL Training Project
A hands-on Python training project with copy/paste code and beginner challenges!

---

## Project Overview

Welcome to WeatherDog, a 3-part project designed to teach you how to use Python to:

1. Fetch live weather data from an API
2. Save that data into a MySQL database
3. Retrieve and format it as JSON (for sharing with other systems)

No virtual environments, no frameworks. Just system Python 3 and MySQL.

---

## Setup Instructions

1) Install Python 3.9+ and MySQL Server (or MariaDB).

2) Install required Python libraries (only once):
```bash
pip install requests mysql-connector-python
```

3) Suggested folder layout:
```
WeatherDog/
├── wd_utils.py
├── phase1_today_weather.py
├── phase2_save_mysql.py
├── phase3_api_json.py
├── weather_schema.sql
└── WeatherDog_Tutorial.md
```

---

## Phase 1 - Fetch and Display Today's Weather

### Objective
- Look up latitude and longitude from a ZIP code (OpenStreetMap Nominatim).
- Fetch today's forecast (Open-Meteo daily).
- Print a readable summary.

### Create wd_utils.py

```python
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")
USER_AGENT = "WeatherDogTrainer/1.0 (student@example.com)"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    51: "Drizzle (light)",
    61: "Rain (slight)",
    63: "Rain (moderate)",
    65: "Rain (heavy)",
    80: "Rain showers (slight)",
    81: "Rain showers (moderate)",
    95: "Thunderstorm",
}

def today_local_iso():
    # Return today's date as YYYY-MM-DD.
    return datetime.now(tz=CHICAGO).date().isoformat()

def geocode_zip(zip_code):
    # Convert a ZIP code to (latitude, longitude) using OpenStreetMap.
    url = "https://nominatim.openstreetmap.org/search"
    params = {"postalcode": zip_code, "country": "USA", "format": "json"}
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"No coordinates found for ZIP {zip_code}")
    return float(data[0]["lat"]), float(data[0]["lon"])

def fetch_today_daily(lat, lon):
    # Fetch today's forecast from Open-Meteo.
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone": "America/Chicago",
        "forecast_days": 1,
        "units": "imperial",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def render_report(zip_code, lat, lon, daily_json):
    # Format forecast into readable text.
    d = daily_json["daily"]
    date = d["time"][0]
    hi = d["temperature_2m_max"][0]
    lo = d["temperature_2m_min"][0]
    prcp = d["precipitation_sum"][0]
    wind = d["windspeed_10m_max"][0]
    code = d["weathercode"][0]
    cond = WEATHER_CODES.get(code, "Unknown")
    return (
        f"lat: {lat:.7f}\n"
        f"lon: {lon:.7f}\n"
        f"Weather Forecast for {date} (ZIP {zip_code}):\n"
        f"Condition: {cond}\n"
        f"High: {hi:.1f} F\nLow: {lo:.1f} F\n"
        f"Precipitation: {prcp:.1f} mm\n"
        f"Max Wind Speed: {wind:.1f} mph\n"
    )
```

### Create phase1_today_weather.py

```python
import argparse
from wd_utils import geocode_zip, fetch_today_daily, render_report, today_local_iso

def main():
    parser = argparse.ArgumentParser(description="WeatherDog Phase 1 - Fetch today's weather")
    parser.add_argument("--zip", default="64093", help="ZIP code to check (default 64093)")
    args = parser.parse_args()

    lat, lon = geocode_zip(args.zip)
    data = fetch_today_daily(lat, lon)

    today = today_local_iso()
    if data["daily"]["time"][0] != today:
        print(f"Warning: API date mismatch (expected {today})")

    print(render_report(args.zip, lat, lon, data))

if __name__ == "__main__":
    main()
```

Run it:
```bash
python3 phase1_today_weather.py --zip 64093
```

Expected output example:
```
lat: 38.7696070
lon: -93.7334748
Weather Forecast for 2025-10-23 (ZIP 64093):
Condition: Overcast
High: 18.8 F
Low: 4.0 F
Precipitation: 0.0 mm
Max Wind Speed: 9.8 mph
```

### Student Challenges (Phase 1)
1) Change the ZIP code to your hometown. What happens?
2) Print only the "Condition" line.
3) Add a new weather code to WEATHER_CODES (example: Snow).
4) Add a command-line argument to switch between imperial and metric.

---

## Phase 2 - Save the Weather to MySQL

### Create weather_schema.sql
```sql
CREATE DATABASE IF NOT EXISTS weatherdog;
USE weatherdog;

CREATE TABLE IF NOT EXISTS weather_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_local DATE NOT NULL,
    zip VARCHAR(10) NOT NULL,
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    condition VARCHAR(64) NOT NULL,
    temp_high_f DECIMAL(4,1) NOT NULL,
    temp_low_f DECIMAL(4,1) NOT NULL,
    precip_mm DECIMAL(6,1) NOT NULL,
    wind_max_mph DECIMAL(5,1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY ux_date_zip (date_local, zip)
);
```

### Create phase2_save_mysql.py

```python
import argparse
import mysql.connector
from wd_utils import geocode_zip, fetch_today_daily

def get_connection(host, user, password, database):
    return mysql.connector.connect(host=host, user=user, password=password, database=database)

def upsert_weather(cur, row):
    sql = (
        "INSERT INTO weather_daily "
        "(date_local, zip, lat, lon, condition, temp_high_f, temp_low_f, precip_mm, wind_max_mph) "
        "VALUES (%(date_local)s, %(zip)s, %(lat)s, %(lon)s, %(condition)s, %(temp_high_f)s, %(temp_low_f)s, %(precip_mm)s, %(wind_max_mph)s) "
        "ON DUPLICATE KEY UPDATE "
        "condition=VALUES(condition), "
        "temp_high_f=VALUES(temp_high_f), "
        "temp_low_f=VALUES(temp_low_f), "
        "precip_mm=VALUES(precip_mm), "
        "wind_max_mph=VALUES(wind_max_mph);"
    )
    cur.execute(sql, row)

def main():
    p = argparse.ArgumentParser(description="WeatherDog Phase 2 - Save to MySQL")
    p.add_argument("--zip", default="64093")
    p.add_argument("--db-host", default="127.0.0.1")
    p.add_argument("--db-user", default="root")
    p.add_argument("--db-pass", default="changeme")
    p.add_argument("--db-name", default="weatherdog")
    args = p.parse_args()

    lat, lon = geocode_zip(args.zip)
    data = fetch_today_daily(lat, lon)
    daily = data["daily"]
    row = {
        "date_local": daily["time"][0],
        "zip": args.zip,
        "lat": lat,
        "lon": lon,
        "condition": "Overcast",
        "temp_high_f": daily["temperature_2m_max"][0],
        "temp_low_f": daily["temperature_2m_min"][0],
        "precip_mm": daily["precipitation_sum"][0],
        "wind_max_mph": daily["windspeed_10m_max"][0],
    }

    conn = get_connection(args.db_host, args.db_user, args.db_pass, args.db_name)
    cur = conn.cursor()
    upsert_weather(cur, row)
    conn.commit()
    print(f"Saved {row['date_local']} for ZIP {row['zip']}")
    conn.close()

if __name__ == "__main__":
    main()
```

### Student Challenges (Phase 2)
1) Change "Overcast" to "Sunny" and re-run it.
2) Run the script twice - what happens? Why no duplicate rows?
3) Add a new column "humidity" and modify the insert to include it.

---

## Phase 3 - Read and Output JSON

### Create phase3_api_json.py

```python
import argparse, json, mysql.connector
from datetime import datetime
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")

def today_local_iso():
    return datetime.now(tz=CHICAGO).date().isoformat()

def get_connection(host, user, password, database):
    return mysql.connector.connect(host=host, user=user, password=password, database=database)

def fetch_for_date(cur, zip_code, date_local):
    sql = "SELECT date_local, zip, lat, lon, condition, temp_high_f, temp_low_f, precip_mm, wind_max_mph FROM weather_daily WHERE zip=%s AND date_local=%s LIMIT 1;"
    cur.execute(sql, (zip_code, date_local))
    row = cur.fetchone()
    if not row:
        return None
    colnames = [d[0] for d in cur.description]
    return dict(zip(colnames, row))

def format_payload(row):
    return {
        "date": str(row["date_local"]),
        "zip": row["zip"],
        "coords": {"lat": float(row["lat"]), "lon": float(row["lon"])},
        "condition": row["condition"],
        "highF": float(row["temp_high_f"]),
        "lowF": float(row["temp_low_f"]),
        "precipMM": float(row["precip_mm"]),
        "windMaxMPH": float(row["wind_max_mph"]),
    }

def main():
    p = argparse.ArgumentParser(description="WeatherDog Phase 3 - Emit JSON")
    p.add_argument("--zip", default="64093")
    p.add_argument("--date", default=today_local_iso())
    p.add_argument("--db-host", default="127.0.0.1")
    p.add_argument("--db-user", default="root")
    p.add_argument("--db-pass", default="changeme")
    p.add_argument("--db-name", default="weatherdog")
    args = p.parse_args()

    conn = get_connection(args.db_host, args.db_user, args.db_pass, args.db_name)
    cur = conn.cursor()
    row = fetch_for_date(cur, args.zip, args.date)
    if not row:
        print(f"No data for {args.date}. Run Phase 2 first.")
        return
    payload = format_payload(row)
    print(json.dumps(payload, indent=2))
    conn.close()

if __name__ == "__main__":
    main()
```

### Student Challenges (Phase 3)
1) Change the JSON key "highF" to "maxTempF".
2) Try printing all records instead of just one.
3) Save the JSON output to a file named "today.json".

---

## Wrap-Up

You built a real-world workflow:
- Fetching data from an API
- Saving to MySQL
- Outputting API-style JSON

Next, try adding graphs, or build a Flask web app to show live results.

Well done!
