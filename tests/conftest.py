"""Fixtures for testing."""

from datetime import timedelta
import json
import os

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weatherapi import coordinator
from custom_components.weatherapi.const import DOMAIN, UPDATE_INTERVAL_MINUTES
from custom_components.weatherapi.coordinator import WeatherAPIUpdateCoordinator
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
def coordinator_config():
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
) -> WeatherAPIUpdateCoordinator:
    """Fixture to provide an instance of WeatherAPIUpdateCoordinator linked to the mock entry."""

    config_entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="id1")
    config_entry.add_to_hass(hass)

    coordinator = WeatherAPIUpdateCoordinator(hass, coordinator_config, config_entry)
    config_entry.runtime_data = coordinator
    return coordinator
