"""Small, extensible registry of data transformers for provider fields.

No dataclasses, no typing module — uses plain classes and utime.

Each transformer is a record with a machine `name`, human `title` and a
`resolve(value)` callable that converts the incoming provider value into the
desired output format.
"""

import utime

OWM_ICON_MAP = {
    "01d": "sun",
    "01n": "moon",
    "02d": "cloud-sun",
    "02n": "cloud-moon",
    "03d": "cloud",
    "03n": "cloud",
    "04d": "clouds",
    "04n": "clouds",
    "09d": "cloud-drizzle",
    "09n": "cloud-drizzle",
    "10d": "cloud-rain",
    "10n": "cloud-rain",
    "11d": "cloud-lightning-rain",
    "11n": "cloud-lightning-rain",
    "13d": "snow",
    "13n": "snow",
    "50d": "cloud-fog2",
    "50n": "cloud-fog2",
}

_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
_WEEKDAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


class Transformer:
    def __init__(self, name, title, resolve):
        self.name = name
        self.title = title
        self.resolve = resolve


def _to_rounded_int(value):
    """Convert a numeric value to a rounded integer.

    Accepts ints, floats and numeric strings. Returns integer on success,
    empty string on invalid input.
    """
    if value is None:
        return ""
    try:
        if isinstance(value, str):
            value = float(value) if "." in value else int(value)
        return int(round(float(value)))
    except Exception:
        return ""


def _unix_to_hhmm(value):
    """Convert a unix timestamp (seconds) to HH:MM string."""
    if value is None:
        return ""
    try:
        ts = int(float(value))
        t = utime.localtime(ts)
        return "{:02d}:{:02d}".format(t[3], t[4])
    except Exception:
        return ""


def _unix_to_day_short_upper(value):
    """Convert a unix timestamp to a short uppercase weekday name (e.g. MON)."""
    if value is None:
        return ""
    try:
        ts = int(float(value))
        t = utime.localtime(ts)
        return _WEEKDAYS_SHORT[t[6]].upper()
    except Exception:
        return ""


def _unix_to_day_with_number(value):
    """Convert a unix timestamp to 'Weekday N' (e.g. 'Sunday 2')."""
    if value is None:
        return ""
    try:
        ts = int(float(value))
        t = utime.localtime(ts)
        return "{} {}".format(_WEEKDAYS[t[6]], t[2])
    except Exception:
        return ""


def _unix_to_month(value):
    """Convert a unix timestamp to full month name (e.g. 'November')."""
    if value is None:
        return ""
    try:
        ts = int(float(value))
        t = utime.localtime(ts)
        return _MONTHS[t[1] - 1]
    except Exception:
        return ""


def _owm_icon(value):
    """Map OpenWeatherMap icon code (e.g. '01d') to local symbol name."""
    if value is None:
        return ""
    try:
        return OWM_ICON_MAP.get(str(value), "")
    except Exception:
        return ""


# Registry of available transformers — key is the name used in provider field config
TRANSFORMERS = {
    "to_rounded_int": Transformer(
        name="to_rounded_int",
        title="Number \u2192 Rounded Integer",
        resolve=_to_rounded_int,
    ),
    "unix_to_hhmm": Transformer(
        name="unix_to_hhmm",
        title="Unix timestamp \u2192 HH:MM",
        resolve=_unix_to_hhmm,
    ),
    "unix_to_day_short_upper": Transformer(
        name="unix_to_day_short_upper",
        title="Unix timestamp \u2192 Short weekday (MON)",
        resolve=_unix_to_day_short_upper,
    ),
    "unix_to_day_with_number": Transformer(
        name="unix_to_day_with_number",
        title="Unix timestamp \u2192 Weekday with day of month (Monday 5)",
        resolve=_unix_to_day_with_number,
    ),
    "unix_to_month": Transformer(
        name="unix_to_month",
        title="Unix timestamp \u2192 Month",
        resolve=_unix_to_month,
    ),
    "owm_icon_code_to_icon": Transformer(
        name="owm_icon_code_to_icon",
        title="OpenWeatherMap icon code \u2192 Icon",
        resolve=_owm_icon,
    ),
}


def get_transformer(name):
    """Return a Transformer by name, or None if not found."""
    return TRANSFORMERS.get(name)


def list_transformers():
    """Return all registered transformers as a list."""
    return list(TRANSFORMERS.values())
