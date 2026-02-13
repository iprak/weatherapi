"""Tests for WeatherAPI integration."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import weatherapi
from custom_components.weatherapi.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_async_load(hass: HomeAssistant) -> None:
    """Test entry load."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="id1",
        data={
            CONF_LATITUDE: 18.10,
            CONF_LONGITUDE: -77.29,
            CONF_API_KEY: "api_key",
            CONF_NAME: "test",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.weatherapi.coordinator.WeatherAPIUpdateCoordinator.get_weather",
        side_effect=AsyncMock(return_value={}),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.LOADED
        assert entry.runtime_data is not None


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_async_unload(hass: HomeAssistant) -> None:
    """Test entry unload."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="id1",
        data={
            CONF_LATITUDE: 18.10,
            CONF_LONGITUDE: -77.29,
            CONF_API_KEY: "api_key",
            CONF_NAME: "test",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.weatherapi.coordinator.WeatherAPIUpdateCoordinator.get_weather",
        side_effect=AsyncMock(return_value={}),
    ):
        await hass.config_entries.async_setup(entry.entry_id)

        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.state is ConfigEntryState.NOT_LOADED
