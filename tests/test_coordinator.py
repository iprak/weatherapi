"""Test WeathreAPI coordinator."""

import asyncio
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock, call, patch

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    Forecast,
)
import pytest

from custom_components.weatherapi import coordinator
from custom_components.weatherapi.const import DATA_FORECAST


@pytest.mark.parametrize(
    "value, result",
    [
        ("1", 1),
        (None, None),
        ("a", None),
    ],
)
def test_to_int(value, result):
    """Test to_int function."""
    assert coordinator.to_int(value) == result


@pytest.mark.parametrize(
    "value, result",
    [
        ("1", 1),
        (None, None),
        ("1.2", 1.2),
        ("1.245", 1.2),
        ("1.255", 1.3),
        ("xzy", None),
    ],
)
def test_to_float(value, result):
    """Test to_float function."""
    assert coordinator.to_float(value) == result


@pytest.mark.parametrize(
    "value, result",
    [
        (None, None),
        # Unit test are not in local timezone
        ("2021-11-25", "2021-11-25T00:00:00+00:00"),
    ],
)
def test_datetime_to_iso(value, result):
    """Test datetime_to_iso function."""
    assert coordinator.datetime_to_iso(value) == result


@pytest.mark.parametrize(
    "value,is_day,result",
    [
        ("1000", True, ATTR_CONDITION_SUNNY),
        ("1000", False, ATTR_CONDITION_CLEAR_NIGHT),
        ("9999999", True, None),
        (None, True, None),
    ],
)
def test_parse_condition_code(value, is_day, result):
    """Test parse_condition_code function."""
    assert coordinator.parse_condition_code(value, is_day) == result


@pytest.mark.parametrize(
    "response_status, json,result",
    [
        (HTTPStatus.NOT_FOUND, None, False),
        (HTTPStatus.OK, {"error": {"code": "12345"}}, False),
        (HTTPStatus.OK, {}, True),
        (HTTPStatus.OK, {"error": {}}, True),
    ],
)
async def test_is_valid_api_key(hass, response_status, json, result):
    """Test is_valid_api_key function."""
    session = Mock()
    response = Mock()
    response.status = response_status
    response.json = AsyncMock(return_value=json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ):
        assert await coordinator.is_valid_api_key(hass, "api_key") == result


async def test_is_valid_api_key_raises_missing_key(hass):
    """Test missing key input for is_valid_api_key."""
    with pytest.raises(coordinator.InvalidApiKey):
        await coordinator.is_valid_api_key(hass, "")


async def test_is_valid_api_key_raises_cannotconnect(hass):
    """Test connection issues for is_valid_api_key."""
    session = Mock()
    session.get = AsyncMock(side_effect=asyncio.TimeoutError)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), pytest.raises(coordinator.CannotConnect):
        await coordinator.is_valid_api_key(hass, "api_key")


@pytest.mark.parametrize(
    "is_metric",
    [
        (True),
        (False),
    ],
)
async def test_constructor(is_metric, coordinator_config):
    """Test coordinator."""
    hass = Mock()
    hass.config.units.is_metric = is_metric

    coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
    assert coord.is_metric == is_metric
    assert coord.location == "latitude,longitude"


async def test_async_update_data_http_error(hass, mock_json, coordinator_config):
    """Test failed coordinator data update."""
    session = Mock()
    response = Mock()
    response.json = AsyncMock(return_value=mock_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
        result = await coord.async_refresh()
        assert result is None


async def test_get_weather_raises_cannotconnect(hass, coordinator_config):
    """Test failed connection for coordinator data update."""
    session = Mock()
    session.get = AsyncMock(side_effect=asyncio.TimeoutError)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), pytest.raises(coordinator.CannotConnect), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
        await coord.get_weather()


async def test_get_weather(hass, mock_json, coordinator_config):
    """Test coordinator data update."""
    session = Mock()
    response = Mock()
    response.status = HTTPStatus.OK
    response.json = AsyncMock(return_value=mock_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
        result = await coord.get_weather()
        assert result
        assert result[DATA_FORECAST]


async def test_get_weather_hourly_forecast(
    hass, mock_json, coordinator_config_hourly_forecast
):
    """Test hourly forecast in coordinator data update."""
    session = Mock()
    response = Mock()
    response.status = HTTPStatus.OK
    response.json = AsyncMock(return_value=mock_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(
            hass, coordinator_config_hourly_forecast
        )
        result = await coord.get_weather()
        assert result
        assert result[DATA_FORECAST]
        assert len(result[DATA_FORECAST]) == 24


async def test_get_weather_hourly_forecast_missing_data(
    hass, mock_json, coordinator_config_hourly_forecast
):
    """Test hourly forecast with data missing."""
    session = Mock()
    response = Mock()
    response.status = HTTPStatus.OK

    hour_forecast_data = mock_json["forecast"]["forecastday"][0]["hour"]
    # Delete `time` element from 2 hourly forecast nodes
    del hour_forecast_data[0]["time"]
    del hour_forecast_data[23]["time"]

    response.json = AsyncMock(return_value=mock_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(
            hass, coordinator_config_hourly_forecast
        )
        result = await coord.get_weather()
        assert result
        assert result[DATA_FORECAST]
        assert len(result[DATA_FORECAST]) == 22

        assert len(coordinator._LOGGER.warning.mock_calls) == 1


async def test_get_weather_no_forecast_data(hass, coordinator_config):
    """Test missing forecast data."""
    session = Mock()
    response = Mock()
    response.status = HTTPStatus.OK
    mock_response_json = {}
    response.json = AsyncMock(return_value=mock_response_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
        result = await coord.get_weather()
        assert result

        assert not result[DATA_FORECAST]  # No data found

        assert len(coordinator._LOGGER.warning.mock_calls) == 2
        assert coordinator._LOGGER.warning.mock_calls[0] == call(
            "No current data received."
        )
        assert coordinator._LOGGER.warning.mock_calls[1] == call(
            "No forecast data received."
        )


async def test_get_weather_no_forecastday_data(hass, coordinator_config):
    """Test missing forecast data."""
    session = Mock()
    response = Mock()
    response.status = HTTPStatus.OK
    mock_response_json = {"forecast": {"dummyNode": "1"}}  # No forecastday
    response.json = AsyncMock(return_value=mock_response_json)
    session.get = AsyncMock(return_value=response)

    with patch.object(
        coordinator,
        "async_get_clientsession",
        return_value=session,
    ), patch.object(coordinator, "_LOGGER"):
        coord = coordinator.WeatherAPIUpdateCoordinator(hass, coordinator_config)
        result = await coord.get_weather()
        assert result

        assert not result[DATA_FORECAST]  # No data found

        assert len(coordinator._LOGGER.warning.mock_calls) == 2
        assert coordinator._LOGGER.warning.mock_calls[0] == call(
            "No current data received."
        )
        assert coordinator._LOGGER.warning.mock_calls[1] == call(
            "No day forecast found in data."
        )


def test_parse_hour_forecast():
    """Test parse_hour_forecast function."""
    assert (
        coordinator.WeatherAPIUpdateCoordinator.parse_hour_forecast(None, True) is None
    )
    # No `time` defined
    assert coordinator.WeatherAPIUpdateCoordinator.parse_hour_forecast({}, True) is None

    data = {
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
    expected = Forecast(
        datetime="2021-11-24T03:00:00+00:00",
        temperature=4.9,
        precipitation_probability=0.2,
        wind_speed=19.0,
        condition=ATTR_CONDITION_CLEAR_NIGHT,
    )
    assert (
        coordinator.WeatherAPIUpdateCoordinator.parse_hour_forecast(data, True)
        == expected
    )

    expected = Forecast(
        datetime="2021-11-24T03:00:00+00:00",
        temperature=40.8,
        precipitation_probability=0.2,
        wind_speed=30.6,
        condition=ATTR_CONDITION_CLEAR_NIGHT,
    )
    assert (
        coordinator.WeatherAPIUpdateCoordinator.parse_hour_forecast(data, False)
        == expected
    )
