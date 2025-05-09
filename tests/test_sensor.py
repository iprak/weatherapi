"""Test WeatherAPI sensor."""

from unittest.mock import Mock

import pytest
import pytest_asyncio

from custom_components.weatherapi.const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND,
)
from custom_components.weatherapi.sensor import WeatherAPISensorEntity
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    ("value", "expected_band"),
    [
        (0, None),
        (1, "Low"),
        (2, "Low"),
        (3, "Low"),
        (4, "Moderate"),
        (5, "Moderate"),
        (6, "Moderate"),
        (7, "High"),
        (8, "High"),
        (9, "High"),
        (10, "Very High"),
        (11, "Very High"),
    ],
)
@pytest_asyncio.fixture
def test_uk_defra_index(hass: HomeAssistant, value, expected_band) -> None:
    """Test UK Defra Index sensor."""
    description = SensorEntityDescription(
        key=ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
        name="UK Defra Index",
        state_class=SensorStateClass.MEASUREMENT,
    )
    location_name = "XYZ"

    coordinator_data = {}
    coordinator_data[ATTR_AIR_QUALITY_UK_DEFRA_INDEX] = value

    mock_coordinator = Mock(data=coordinator_data, hass=hass)

    sensor = WeatherAPISensorEntity(location_name, mock_coordinator, description)
    assert sensor.native_value == value

    if expected_band is None:
        assert sensor.extra_state_attributes is None
    else:
        assert sensor.extra_state_attributes == {
            ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND: expected_band
        }
