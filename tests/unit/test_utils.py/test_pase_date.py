import pytest
from datetime import datetime, timezone

from src.utils import parse_date_to_timestamp_ms


def test_parse_int_timestamp_ms():
    assert parse_date_to_timestamp_ms(10**13) == 10**13  # ya está en ms

def test_parse_int_timestamp_seconds():
    assert parse_date_to_timestamp_ms(1600000000) == 1600000000 * 1000  # seconds to ms

def test_parse_float_timestamp_seconds():
    assert parse_date_to_timestamp_ms(1600000000.123) == int(1600000000.123 * 1000)

def test_parse_iso_string_with_timezone():
    iso = "2023-06-28T12:00:00+00:00"
    expected = int(datetime.fromisoformat(iso).timestamp() * 1000)
    assert parse_date_to_timestamp_ms(iso) == expected

def test_parse_iso_string_without_timezone():
    iso = "2023-06-28T12:00:00"
    dt = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    expected = int(dt.timestamp() * 1000)
    assert parse_date_to_timestamp_ms(iso) == expected

def test_parse_datetime_with_tz():
    dt = datetime(2023, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    expected = int(dt.timestamp() * 1000)
    assert parse_date_to_timestamp_ms(dt) == expected

def test_parse_datetime_without_tz():
    dt = datetime(2023, 6, 28, 12, 0, 0)
    dt = dt.replace(tzinfo=timezone.utc)
    expected = int(dt.timestamp() * 1000)
    assert parse_date_to_timestamp_ms(dt) == expected

def test_parse_invalid_string_raises_value_error():
    with pytest.raises(ValueError):
        parse_date_to_timestamp_ms("not a date")

def test_parse_invalid_type_raises_value_error():
    with pytest.raises(ValueError):
        parse_date_to_timestamp_ms(["invalid", "type"])
