"""Tests for WeatherAPI integration."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME

from custom_components import weatherapi
from custom_components.weatherapi.const import DOMAIN

from tests.common import MockConfigEntry


async def test_async_unload_entry(hass, enable_custom_integrations):
    """Test entry unload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 18.10,
            CONF_LONGITUDE: -77.29,
            CONF_API_KEY: "api_key",
            CONF_NAME: "test",
        },
    )

    with patch(
        "custom_components.weatherapi.coordinator.WeatherAPIUpdateCoordinator.get_weather",
        side_effect=AsyncMock(return_value={}),
    ):
        await weatherapi.async_setup_entry(hass, entry)

        assert hass.data[DOMAIN].get(entry.entry_id) is not None

        await weatherapi.async_unload_entry(hass, entry)
        assert hass.data[DOMAIN].get(entry.entry_id) is None
