"""Test WeatherAPI coordinator."""

import asyncio
from http import HTTPStatus
import logging

import aiohttp
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.weatherapi import config_flow, coordinator
from custom_components.weatherapi.const import (
    DAILY_FORECAST,
    FORECAST_URL,
    HOURLY_FORECAST,
    TIMEZONE_URL,
)
from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    Forecast,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed


@pytest.mark.parametrize(
    ("value", "result"),
    [
        ("1", 1),
        (None, None),
        ("a", None),
    ],
)
def test_to_int(value, result) -> None:
    """Test to_int function."""
    assert coordinator.to_int(value) == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        ("1", 1),
        (None, None),
        ("1.2", 1.2),
        ("1.245", 1.2),
        ("1.255", 1.3),
        ("xzy", None),
    ],
)
def test_to_float(value, result) -> None:
    """Test to_float function."""
    assert coordinator.to_float(value) == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (None, None),
        # Unit test are not in local timezone
        ("2021-11-25", "2021-11-25T00:00:00+00:00"),
    ],
)
def test_datetime_to_iso(value, result) -> None:
    """Test datetime_to_iso function."""
    assert coordinator.datetime_to_iso(value) == result


@pytest.mark.parametrize(
    ("value", "is_day", "result"),
    [
        ("1000", True, ATTR_CONDITION_SUNNY),
        ("1000", False, ATTR_CONDITION_CLEAR_NIGHT),
        ("9999999", True, None),
        (None, True, None),
    ],
)
def test_parse_condition_code(value, is_day, result) -> None:
    """Test parse_condition_code function."""
    assert coordinator.parse_condition_code(value, is_day) == result


@pytest.mark.parametrize(
    ("response_status", "json", "result"),
    [
        (HTTPStatus.OK, {"error": {"code": "12345"}}, False),
        (HTTPStatus.OK, {}, True),
        (HTTPStatus.OK, {"error": {}}, True),
    ],
)
async def test_is_valid_api_key(
    hass: HomeAssistant,
    response_status,
    json,
    result,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test is_valid_api_key function."""

    aioclient_mock.get(
        TIMEZONE_URL,
        json=json,
        status=response_status,
    )
    assert await config_flow.is_valid_api_key(hass, "api_key") == result


async def test_is_valid_api_key_raises_missing_key(hass: HomeAssistant) -> None:
    """Test missing key input for is_valid_api_key."""
    with pytest.raises(config_flow.InvalidApiKey):
        await config_flow.is_valid_api_key(hass, "")


async def test_is_valid_api_key_raises_cannotconnect(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test connection issues for is_valid_api_key."""

    aioclient_mock.get(
        TIMEZONE_URL,
        exc=aiohttp.ClientError,
    )
    with pytest.raises(config_flow.CannotConnect):
        await config_flow.is_valid_api_key(hass, "api_key")


async def test_async_update_data_http_error(
    mock_json,
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test failed coordinator data update."""
    aioclient_mock.get(
        TIMEZONE_URL, json=mock_json, status=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    result = await mock_coordinator.async_refresh()
    assert result is None


async def test_get_weather_raises_cannotconnect(
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test failed connection for coordinator data update."""
    aioclient_mock.get(
        FORECAST_URL,
        exc=asyncio.TimeoutError,
    )

    with pytest.raises(UpdateFailed):
        await mock_coordinator.get_weather()


async def test_get_weather(
    mock_json,
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test coordinator data update."""
    aioclient_mock.get(
        FORECAST_URL,
        json=mock_json,
    )

    result = await mock_coordinator.get_weather()
    assert result
    assert result[DAILY_FORECAST]
    assert result[HOURLY_FORECAST]


async def test_get_weather_hourly_forecast(
    mock_json,
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test hourly forecast in coordinator data update."""
    aioclient_mock.get(
        FORECAST_URL,
        json=mock_json,
    )

    result = await mock_coordinator.get_weather()
    assert result
    assert result[DAILY_FORECAST]
    assert len(result[DAILY_FORECAST]) == 1


async def test_get_weather_hourly_forecast_missing_data(
    mock_json,
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test hourly forecast with data missing."""

    hour_forecast_data = mock_json["forecast"]["forecastday"][0]["hour"]
    # Delete `time` element from 2 hourly forecast nodes
    del hour_forecast_data[0]["time_epoch"]
    del hour_forecast_data[23]["time_epoch"]

    aioclient_mock.get(
        FORECAST_URL,
        json=mock_json,
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    result = await mock_coordinator.get_weather()
    assert result
    assert result[DAILY_FORECAST]
    assert len(result[DAILY_FORECAST]) == 1

    assert len(caplog.record_tuples) == 1


async def test_get_weather_no_forecast_data(
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test missing forecast data."""
    aioclient_mock.get(
        FORECAST_URL,
        json={},
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    result = await mock_coordinator.get_weather()
    assert result

    assert not result[DAILY_FORECAST]  # No data found
    assert not result[HOURLY_FORECAST]  # No data found

    assert len(caplog.record_tuples) == 3

    assert caplog.record_tuples[0][1] == logging.WARNING
    assert "No current data received" in caplog.record_tuples[0][2]

    assert caplog.record_tuples[1][1] == logging.WARNING
    assert "No forecast data received" in caplog.record_tuples[1][2]


async def test_get_weather_no_forecastday_data(
    mock_coordinator,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test missing forecast data."""
    aioclient_mock.get(
        FORECAST_URL,
        json={"forecast": {"dummyNode": "1"}},  # No forecastday
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    result = await mock_coordinator.get_weather()
    assert result

    assert not result[DAILY_FORECAST]  # No data found
    assert not result[HOURLY_FORECAST]  # No data found

    assert len(caplog.record_tuples) == 3

    assert caplog.record_tuples[0][1] == logging.WARNING
    assert "No current data received" in caplog.record_tuples[0][2]

    assert caplog.record_tuples[1][1] == logging.WARNING
    assert "No day forecast found in data" in caplog.record_tuples[1][2]


sample_data_for_parse_hour_forecast = {
    "time_epoch": 1637744400,
    "time": "2021-11-24 03:00",
    "temp_c": 4.9,
    "temp_f": 40.8,
    "is_day": 0,
    "condition": {
        "text": "Clear",
        "icon": "//cdn.weatherapi.com/weather/64x64/night/113.png",
        "code": 1000,
    },
    "wind_mph": 19.0,
    "wind_kph": 30.6,
    "wind_degree": 196,
    "wind_dir": "SSW",
    "pressure_mb": 1016.0,
    "pressure_in": 30.0,
    "precip_mm": 0.0,
    "precip_in": 0.0,
    "humidity": 53,
    "cloud": 3,
    "feelslike_c": -0.1,
    "feelslike_f": 31.8,
    "windchill_c": -0.1,
    "windchill_f": 31.8,
    "heatindex_c": 4.9,
    "heatindex_f": 40.8,
    "dewpoint_c": -3.7,
    "dewpoint_f": 25.3,
    "will_it_rain": 0,
    "chance_of_rain": 0.2,
    "will_it_snow": 0,
    "chance_of_snow": 0,
    "vis_km": 10.0,
    "vis_miles": 6.0,
    "gust_mph": 27.7,
    "gust_kph": 44.6,
    "uv": 1.0,
}


@pytest.mark.parametrize(
    ("zone", "data", "expected"),
    [
        ("UTC", None, None),
        ("UTC", {}, None),
        (
            "UTC",
            sample_data_for_parse_hour_forecast,
            [
                True,
                Forecast(
                    datetime="2021-11-24T09:00:00+00:00",
                    precipitation_probability=0.2,
                    native_precipitation=0.0,
                    native_pressure=1016.0,
                    native_temperature=4.9,
                    wind_bearing="SSW",
                    native_wind_speed=30.6,
                    condition=ATTR_CONDITION_CLEAR_NIGHT,
                    reported_condition=1000,
                ),
            ],
        ),
    ],
)
def test_parse_hour_forecast(
    zone,
    data,
    expected,
    mock_coordinator,
) -> None:
    """Test parse_hour_forecast function."""

    mock_coordinator.populate_time_zone(zone)
    assert mock_coordinator.parse_hour_forecast(data) == expected
