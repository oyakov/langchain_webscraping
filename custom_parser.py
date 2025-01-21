import re
from datetime import datetime, timedelta

def parse_serbian_relative_time(text):
    """
    Parse Serbian relative time expressions like:
      - "pre 5 minuta"   -> 5 minutes ago
      - "pre 2 sata"     -> 2 hours ago
      - "pre 1 dan"      -> 1 day ago
      - "pre 10 sekundi" -> 10 seconds ago

    Returns a datetime object approximating the time that many units ago,
    or None if the text doesn't match the expected pattern.
    """
    # Regex to capture something like: "pre <number> <word>"
    match = re.match(r"pre\s+(\d+)\s+(\w+)", text)
    if not match:
        print("None found")
        return None

    quantity = int(match.group(1))
    unit = match.group(2).lower()
    print(quantity)
    print(unit)

    # Map from Serbian time units to either `timedelta` arguments or
    # approximate English equivalents. Add or adjust as needed.
    # Note: Some words have multiple forms in Serbian based on singular/plural:
    #   - sekunda, sekunde, sekundi
    #   - minut, minuta, minute
    #   - sat, sata, sati
    #   - dan, dana
    #   - nedelja, nedelje, nedelja
    #   - mesec, meseca, meseci
    # etc.
    serbian_to_timedelta = {
        # seconds
        "sekundi": "seconds",
        "sekunde": "seconds",
        "sekunda": "seconds",
        # minutes
        "minuta": "minutes",
        "minut":  "minutes",
        # hours
        "sata":   "hours",
        "sat":    "hours",
        "sati":   "hours",
        # days
        "dana":   "days",
        "dan":    "days",
        # weeks (if needed)
        "nedelja": "weeks",
        "nedelje": "weeks",
        # months (approximated)
        "mesec":  "days",
        "meseca": "days",
        # years (also approximated)
        "godina": "days",  # or you could use e.g. "days": 365, etc.
    }

    if unit not in serbian_to_timedelta:
        return None

    time_unit = serbian_to_timedelta[unit]

    # For months, years, or any bigger chunks, you may want a more precise approach
    # like dateutil.relativedelta; but here's a rough approximation:
    if time_unit == "days" and unit.startswith("mesec"):
        # Approximate 1 month as ~30 days
        delta = timedelta(days=30 * quantity)
    elif time_unit == "days" and unit.startswith("godin"):
        # Approximate 1 year as ~365 days
        delta = timedelta(days=365 * quantity)
    elif time_unit == "weeks":
        # 1 week = 7 days
        delta = timedelta(weeks=quantity)
    else:
        # For seconds, minutes, hours, days directly
        delta = timedelta(**{time_unit: quantity})

    return datetime.now() - delta