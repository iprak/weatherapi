"""Tests for WeatherAPI integration."""
from datetime import timedelta
import json
import os

from homeassistant import loader
import pytest

from custom_components.weatherapi import coordinator
from custom_components.weatherapi.const import UPDATE_INTERVAL_MINUTES


def load_json(filename):
    """Load sample JSON."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()


@pytest.fixture
def mock_json():
    """Return sample JSON data with 24 hourly forecast and 1 day forecast."""
    yield json.loads(load_json("response.json"))


@pytest.fixture
def coordinator_config():
    """Return a mock coordinator configuration."""
    yield coordinator.WeatherAPIUpdateCoordinatorConfig(
        api_key="api_key",
        location="latitude,longitude",
        name="Place",
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
    )


@pytest.fixture
def coordinator_config_hourly_forecast():
    """Return a mock coordinator configuration."""
    yield coordinator.WeatherAPIUpdateCoordinatorConfig(
        api_key="api_key",
        location="latitude,longitude",
        name="Place",
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        hourly_forecast=True,
    )


@pytest.fixture
def enable_custom_integrations(hass):
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)
