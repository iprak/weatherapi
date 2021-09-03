"""Test WeathreAPI coordinator."""

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.const import HTTP_NOT_FOUND, HTTP_OK
import pytest
from unittest.mock import Mock, patch, AsyncMock
from custom_components.weatherapi import coordinator


@pytest.mark.parametrize(
    "value, result",
    [
        ("1", 1),
        (None, None),
        ("a", None),
    ],
)
def test_to_int(value, result):
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
