"""Real forecast from Open-Meteo (free, no key): geocode the place, then the daily forecast.

https://open-meteo.com/en/docs. Only the place name and the date leave the machine.
"""

import json
import urllib.parse
import urllib.request
from datetime import date as Date

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
# WMO weather codes, grouped
CONDITIONS = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
              51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain",
              65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
              81: "rain showers", 82: "violent rain showers", 95: "thunderstorm", 96: "thunderstorm with hail",
              99: "thunderstorm with hail"}


def _get(url: str, params: dict, timeout: float) -> dict:
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "pocketagent-demo"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def open_meteo(place: str, date: str | None, language: str = "en", timeout: float = 4.0) -> dict:
    """Forecast for place on date (ISO, default today). Raises if the place or the date is not found."""
    geo = _get(GEOCODE, {"name": place, "count": 1, "language": language, "format": "json"}, timeout)
    if not geo.get("results"):
        raise LookupError(f"place not found: {place}")
    loc = geo["results"][0]
    fc = _get(FORECAST, {"latitude": loc["latitude"], "longitude": loc["longitude"], "timezone": "auto",
                         "forecast_days": 16, "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                                                        "precipitation_probability_max"}, timeout)
    daily = fc["daily"]
    day = date or Date.today().isoformat()
    if day not in daily["time"]:
        raise LookupError(f"no forecast for {day}")
    i = daily["time"].index(day)
    code = daily["weather_code"][i]
    return {"place": ", ".join(x for x in [loc.get("name"), loc.get("country")] if x), "date": day,
            "condition": CONDITIONS.get(code, "mixed"), "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precipitation_chance": daily["precipitation_probability_max"][i], "source": "Open-Meteo"}
