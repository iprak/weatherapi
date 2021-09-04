"""Tests for WeatherAPI integration."""
from datetime import timedelta
import json
import os

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
    """Return sample JSON data."""
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
