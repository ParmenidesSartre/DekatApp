from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
import re
from typing import Optional

from django.utils import timezone


@dataclass(frozen=True)
class HoursWindow:
    opens_at: time
    closes_at: time


_HOURS_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\s*-\s*(?P<end>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)"
)


def _parse_time(value: str) -> Optional[time]:
    value = value.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def parse_operating_hours(value: str | None) -> Optional[HoursWindow]:
    if not value:
        return None
    match = _HOURS_RANGE_RE.search(value)
    if not match:
        return None

    start = _parse_time(match.group("start"))
    end = _parse_time(match.group("end"))
    if not start or not end:
        return None

    return HoursWindow(opens_at=start, closes_at=end)


def is_open_now(operating_hours: str | None, *, now: Optional[datetime] = None) -> Optional[bool]:
    window = parse_operating_hours(operating_hours)
    if not window:
        return None

    now = now or timezone.localtime()
    now_t = now.time()

    if window.opens_at <= window.closes_at:
        return window.opens_at <= now_t <= window.closes_at

    # Overnight window (e.g. 8:00 PM - 2:00 AM)
    return now_t >= window.opens_at or now_t <= window.closes_at

