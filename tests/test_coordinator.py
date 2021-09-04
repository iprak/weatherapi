"""Test WeathreAPI coordinator."""

import asyncio
from unittest.mock import AsyncMock, Mock, call, patch

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.const import HTTP_NOT_FOUND, HTTP_OK
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
        (HTTP_NOT_FOUND, None, False),
        (HTTP_OK, {"error": {"code": "12345"}}, False),
        (HTTP_OK, {}, True),
        (HTTP_OK, {"error": {}}, True),
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


async def test_is_valid_api_key_raises_CannotConnect(hass):
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


async def test_async_update_data_HTTP_NOT_FOUND(hass, mock_json, coordinator_config):
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


async def test_get_weather_raises_CannotConnect(hass, coordinator_config):
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
    response.status = HTTP_OK
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


async def test_get_weather_no_forecast_data(hass, coordinator_config):
    """Test missing forecast data."""
    session = Mock()
    response = Mock()
    response.status = HTTP_OK
    mock_json = {}
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
    response.status = HTTP_OK
    mock_json = {"forecast": {"dummyNode": "1"}}  # No forecastday
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

        assert not result[DATA_FORECAST]  # No data found

        assert len(coordinator._LOGGER.warning.mock_calls) == 2
        assert coordinator._LOGGER.warning.mock_calls[0] == call(
            "No current data received."
        )
        assert coordinator._LOGGER.warning.mock_calls[1] == call(
            "No day forecast found in data."
        )
