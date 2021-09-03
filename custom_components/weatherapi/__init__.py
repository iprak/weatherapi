"""The WeatherAPI integration."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.weatherapi.const import DOMAIN, UPDATE_INTERVAL_MINUTES
from custom_components.weatherapi.coordinator import (
    WeatherAPIUpdateCoordinator,
    WeatherAPIUpdateCoordinatorConfig,
)

PLATFORMS = ["weather"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the WeatherAPI component."""

    hass.data.setdefault(DOMAIN, {})

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    config = WeatherAPIUpdateCoordinatorConfig(
        api_key=entry.data[CONF_API_KEY],
        location=f"{latitude},{longitude}",
        name=entry.data[CONF_NAME],
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
    )
    coordinator = WeatherAPIUpdateCoordinator(hass, config)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))
    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
