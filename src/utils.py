from datetime import datetime, timezone
from dateutil.parser import parse as parse_date


def parse_date_to_timestamp_ms(value) -> int:
    """
    Converts a datetime, ISO string or timestamp (seconds or ms) to timestamp in milliseconds.
    If already an int timestamp in ms, returns as is.
    """
    try:
        if value is None:
            return None

        if isinstance(value, int):
            # Could be seconds or milliseconds, assume milliseconds if > 10**12 else seconds
            if value > 10**12:
                return value
            return value * 1000

        if isinstance(value, float):
            # Treat as seconds float
            return int(value * 1000)

        if isinstance(value, str):
            dt = parse_date(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)

        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        
    except Exception as e:
        raise ValueError(e)

    raise ValueError(f"Cannot parse to timestamp ms: {value}")


def parse_to_timestamp_ms_now() -> int:
    """Returns current UTC timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)
