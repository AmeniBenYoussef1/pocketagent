"""The tools the agent can run, on an in-memory backend.

Everything is a mock except the weather, which can use a real forecast
(backend.weather_provider, see weather.py) and falls back to a fake one.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class MockBackend:
    alarms: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    drafts: list[dict] = field(default_factory=list)
    outbox: list[dict] = field(default_factory=list)
    playing: dict | None = None
    # (place, iso date or None, language) -> forecast dict; None keeps the fake forecast
    weather_provider: Callable[[str, str | None, str], dict] | None = field(default=None, compare=False)
    home_city: str = field(default="Tunis", compare=False)


def alarm_set(backend: MockBackend, time: str, date: str | None = None, **_) -> dict:
    alarm = {"id": len(backend.alarms) + 1, "time": time, "date": date}
    backend.alarms.append(alarm)
    return alarm


def fake_forecast(place: str, date: str | None) -> dict:
    """Deterministic: same place and date, same answer."""
    seed = int(hashlib.md5(f"{place}|{date}".encode()).hexdigest(), 16)
    return {"place": place, "date": date, "condition": ["sunny", "cloudy", "rain", "windy"][seed % 4],
            "temp_c": 10 + seed % 20, "source": "offline estimate"}


def weather_query(backend: MockBackend, place_name: str | None = None, date: str | None = None,
                  language: str = "en", **_) -> dict:
    """Real forecast when a provider is set and reachable, the fake one otherwise."""
    if backend.weather_provider is None:
        return {k: v for k, v in fake_forecast(place_name or "current location", date).items() if k != "source"}
    place = place_name or backend.home_city
    try:
        return backend.weather_provider(place, date, language)
    except Exception as e:  # network down, unknown place, date out of range
        return {**fake_forecast(place, date), "note": f"live forecast unavailable ({type(e).__name__})"}


def calendar_set(backend: MockBackend, event_name: str, date: str, time: str | None = None, **_) -> dict:
    event = {"id": len(backend.events) + 1, "event_name": event_name, "date": date, "time": time}
    backend.events.append(event)
    return event


def play_music(backend: MockBackend, song_name: str | None = None, artist_name: str | None = None,
               music_genre: str | None = None, playlist_name: str | None = None, **_) -> dict:
    """Mock player: records what would be playing."""
    backend.playing = {"song": song_name, "artist": artist_name, "genre": music_genre,
                       "playlist": playlist_name, "shuffle": not any([song_name, artist_name, music_genre, playlist_name])}
    return backend.playing


def email_draft(backend: MockBackend, person: str | None = None, relation: str | None = None,
                email_address: str | None = None, event_name: str | None = None, **_) -> dict:
    """Sensitive: the first call only writes a draft."""
    draft = {"id": len(backend.drafts) + 1, "to": email_address or person or relation,
             "subject": event_name, "sent": False}
    backend.drafts.append(draft)
    return draft


def email_send(backend: MockBackend, draft_id: int) -> dict:
    """Send a draft (mock): only called after explicit confirmation."""
    draft = next(d for d in backend.drafts if d["id"] == draft_id)
    draft["sent"] = True
    backend.outbox.append(draft)
    return draft


def email_cancel(backend: MockBackend, draft_id: int) -> dict:
    draft = next(d for d in backend.drafts if d["id"] == draft_id)
    backend.drafts.remove(draft)
    return {**draft, "cancelled": True}


TOOL_FUNCTIONS = {
    "alarm_set": alarm_set,
    "weather_query": weather_query,
    "calendar_set": calendar_set,
    "play_music": play_music,
    "email_sendemail": email_draft,
}
