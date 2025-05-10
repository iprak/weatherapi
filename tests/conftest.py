"""Fixtures for testing."""

from datetime import timedelta
import json
import os

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weatherapi import coordinator
from custom_components.weatherapi.const import UPDATE_INTERVAL_MINUTES
from homeassistant.core import HomeAssistant


def load_json(filename):
    """Load sample JSON."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()


@pytest.fixture
def mock_json():
    """Return sample JSON data with 24 hourly forecast and 1 day forecast."""
    return json.loads(load_json("response.json"))


@pytest.fixture
def coordinator_config() -> coordinator.WeatherAPIUpdateCoordinatorConfig:
    """Return a mock coordinator configuration."""
    return coordinator.WeatherAPIUpdateCoordinatorConfig(
        api_key="api_key",
        location="latitude,longitude",
        name="Place",
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        ignore_past_forecast=False,  # Our test data has old timestamps
    )


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant, coordinator_config
) -> coordinator.WeatherAPIUpdateCoordinator:
    """Return a mock coordinator."""
    return coordinator.WeatherAPIUpdateCoordinator(
        hass, coordinator_config, MockConfigEntry()
    )
