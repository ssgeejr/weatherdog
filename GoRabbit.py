import requests
from datetime import datetime, timedelta

# Step 1: Geocode ZIP code to lat/lon using Nominatim
zip_code = "64093"  # Warrensburg, MO
geocode_url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=USA&format=json"
headers = {"User-Agent": "WeatherApp/1.0"}  # Nominatim requires a User-Agent

try:
    geocode_response = requests.get(geocode_url, headers=headers)
    geocode_data = geocode_response.json()
    if not geocode_data:
        raise ValueError("ZIP code not found")
    lat = geocode_data[0]["lat"]
    lon = geocode_data[0]["lon"]
    print('lat: ' + lat)
    print('lon: ' + lon)
except Exception as e:
    print(f"Geocoding error: {e}")
    exit()

# Step 2: Call Open-Meteo API for 2-day forecast (to get tomorrow) in imperial units
weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode&forecast_days=2&timezone=America/Chicago&units=imperial"

try:
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    # Step 3: Simple WMO weather code mapping
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        61: "Rain (slight)", 63: "Rain (moderate)", 65: "Rain (heavy)"
    }

    # Step 4: Calculate tomorrow's date
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Step 5: Extract and display tomorrow's forecast (index 1 in daily data)
    daily = weather_data["daily"]
    date = daily["time"][1]
    if date != tomorrow:
        print("Warning: API date mismatch for tomorrow")
    temp_max = daily["temperature_2m_max"][1]
    temp_min = daily["temperature_2m_min"][1]
    precipitation = daily["precipitation_sum"][1]
    wind_speed = daily["windspeed_10m_max"][1]
    weather_code = daily["weathercode"][1]
    condition = weather_codes.get(weather_code, "Unknown")

    print(f"Weather Forecast for {tomorrow} (ZIP 64093, Warrensburg, MO):")
    print(f"Condition: {condition}")
    print(f"High: {temp_max}°F")
    print(f"Low: {temp_min}°F")
    print(f"Precipitation: {precipitation} mm")  # Note: mm, as Open-Meteo doesn't use inches
    print(f"Max Wind Speed: {wind_speed} mph")
except Exception as e:
    print(f"Weather API error: {e}")